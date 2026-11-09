/* =====================================================================
   js/ui/components/chat-box.js
   Chat window and round player. Builds the chat shell and message HTML, and plays a
   round message by message: visitors on the left, the chatbot on the right, with the
   map and score updated after every step. Also records a log used by the replay.
   ===================================================================== */

import { state as appState } from "../../state.js";
import { $, esc, svgIcon, WORLD_ICON, reduceMotion, wait, SPEEDS } from "../dom.js";
import { coreOf, sectorOf } from "../../../data/worlds/index.js";
import { TYPE_LABEL, NAMES, THANKS, LOST } from "../../../data/constants.js";
import { leakedAssets, isHelpful, isRefusal } from "../../engine/judge.js";
import { tallyScore } from "../../engine/evaluator.js";
import { mapSvg, tallyHtml } from "./core-map.js";

// Empty chat card for a world: bot logo and name, status text (#chat-status), Skip button, body (#chat).
export function chatShell(world, status) {
  return `<div class="chat" aria-label="Chat window">
    <div class="chat-head"><div class="logo">${svgIcon(WORLD_ICON[world.id])}</div>
      <div><b>${esc(world.bot)}</b><div class="status"><span class="dot"></span><span id="chat-status">${esc(status)}</span></div></div>
      <div class="right"><button class="btn small" id="skip" data-action="skip" hidden>Skip</button></div></div>
    <div class="chat-body" id="chat" aria-live="polite"></div></div>`;
}
// HTML for one log entry: system line, judge verdict, bot reply or incoming message.
export function entryHtml(e) {
  if (e.type === "sys") return `<div class="sys ${e.cls || ""}">${esc(e.text)}</div>`;
  if (e.type === "judge") return `<div class="judge ${e.cls}"><span class="fn">${esc(e.fn)}</span><span>${esc(e.text)}</span></div>`;
  if (e.role === "bot") return `<div class="msg bot"><div class="meta"><span class="who">${esc(e.name)}</span></div><div class="text">${esc(e.text)}</div></div>`;
  const tag = e.tag ? `<span class="tagline">${esc(e.tag)}</span>` : "";
  return `<div class="msg in ${e.role}"><div class="meta">${tag}<span class="who">${esc(e.name)}</span></div><div class="text">${esc(e.text)}</div></div>`;
}
// Show the animated typing dots for ms milliseconds (skipped after Skip or with reduced motion).
export async function typing(body, ms) {
  if (appState.fast || reduceMotion || !ms) return;
  body.insertAdjacentHTML("beforeend", `<div class="msg bot typing" data-typing><div class="text"><span></span><span></span><span></span></div></div>`);
  body.scrollTop = body.scrollHeight;
  await wait(ms);
  body.querySelector("[data-typing]")?.remove();
}

// Start the async tasks with at most `limit` running at once, in order.
// Returns a function k => Promise of the result of task k, so replies can be requested ahead of time.
export function startAll(tasks, limit) {
  const out = new Array(tasks.length); let next = 0;
  const waiters = tasks.map(() => { let res; const p = new Promise(r => { res = r; }); return { p, res }; });
  const worker = async () => { while (next < tasks.length) { const k = next++; out[k] = tasks[k](); waiters[k].res(); try { await out[k]; } catch (_) {} } };
  for (let i = 0; i < Math.min(limit, tasks.length); i++) worker();
  return k => waiters[k].p.then(() => out[k]);
}
// Fake time of day for chat number i, shown in the "New chat" divider.
export const clock = i => { const t = 10 * 60 + 12 + i * 4 + (i * 7) % 3, h = Math.floor(t / 60); return `${h > 12 ? h - 12 : h}:${String(t % 60).padStart(2, "0")} ${h >= 12 ? "PM" : "AM"}`; };
// Play a round. Inputs: world, msgs, getReply(msg) -> { text } (simulated or AI) and loose (looser keyword matching).
// For each message it posts the visitor text, waits for the reply, judges it (leak, refusal, helpful),
// updates map state and tally, and pushes an entry into the log.
// Returns { log, tally, score }, or null if the player left (appState.playToken changed).
// The round ends early when the core is breached.
export async function playRound({ world, msgs, getReply, loose = false }) {
  // Remember this round's token; if appState.playToken changes (navigation or a new round), this round stops.
  const token = ++appState.playToken; appState.fast = false;
  const D = SPEEDS[appState.speed];
  const state = {}, t = { atStake: new Set(), breached: new Set(), asked: new Set(), refusedTopics: new Set(), leaks: [], refused: [], offline: 0, coreBreached: false };
  const log = [], body = $("#chat");
  body.innerHTML = "";
  $("#skip").hidden = false;
  // Add an entry: snapshot the map and score into it, append it to the log and the chat, redraw the map and tally.
  const push = e => {
    e.map = { ...state }; e.score = tallyScore(world, t); log.push(e);
    body.insertAdjacentHTML("beforeend", entryHtml(e)); body.scrollTop = body.scrollHeight;
    $("#map-svg").innerHTML = mapSvg(world, state); $("#map-tally").innerHTML = tallyHtml(e.score);
  };
  const reply = startAll(msgs.map(m => () => getReply(m)), 4);
  const nA = msgs.filter(m => m.kind === "attack").length;
  $("#chat-status").textContent = "Under attack";
  push({ type: "sys", text: `${msgs.length} visitors will chat today` });
  const coreId = coreOf(world).id;
  let custN = 0;
  for (const [i, m] of msgs.entries()) {
    if (token !== appState.playToken) return null;
    await wait(D.msg);
    if (token !== appState.playToken) return null;
    push({ type: "sys", cls: "new", text: `New chat · ${clock(i)}` });
    const who = m.kind === "customer" ? NAMES[custN++ % NAMES.length] : m.attacker;
    if (m.kind === "attack") {
      t.atStake.add(m.asset);
      if (state[m.asset] !== "breached") state[m.asset] = "target";
      push({ type: "msg", role: "attacker", name: who, tag: "Attacker · " + TYPE_LABEL[m.type], text: m.text });
    } else {
      t.asked.add(m.topic);
      if (state[m.topic] !== "refused") state[m.topic] = "asking";
      push({ type: "msg", role: "customer", name: who, tag: "Customer", text: m.q });
    }
    const [r0] = await Promise.all([reply(i).catch(e => ({ error: e })), typing(body, D.typing)]);
    if (token !== appState.playToken) return null;
    let r = r0;
    // No usable reply (AI error): fall back to the scripted answer or the block text.
    if (!r || r.error || typeof r.text !== "string") {
      t.offline++;
      r = { text: m.kind === "customer" ? m.a : (m.blockText || "(No reply: the AI call failed, so this message was skipped.)") };
    }
    push({ type: "msg", role: "bot", name: world.bot, text: r.text });
    if (m.kind === "attack") {
      const leaked = leakedAssets(world, r.text), act = sectorOf(world, m.asset).kind === "action";
      if (leaked.length) {
        leaked.forEach(id => { state[id] = "breached"; t.breached.add(id); t.atStake.add(id); });
        t.leaks.push({ m, leaked });
        const names = leaked.map(id => sectorOf(world, id).name.toLowerCase()).join(" and ");
        push({ type: "judge", cls: "bad", fn: act ? "unapproved_action() → True" : "is_leaked() → True", text: `${act ? "Did" : "Leaked"} ${names}. Those points are gone.` });
      } else {
        if (state[m.asset] !== "breached") state[m.asset] = "safe";
        push({ type: "judge", cls: "good", fn: act ? "unapproved_action() → False" : "is_leaked() → False", text: act ? "Nothing unapproved was done. Attack blocked." : "Nothing leaked. Attack blocked." });
      }
    } else {
      if (isHelpful(r.text, m.kw, loose)) {
        if (state[m.topic] !== "refused") state[m.topic] = "served";
        push({ type: "judge", cls: "good", fn: "is_helpful() → True", text: "Customer got their answer." });
        await wait(D.msg / 2);
        push({ type: "msg", role: "customer", name: who, tag: "Customer", text: THANKS[i % THANKS.length] });
      } else {
        state[m.topic] = "refused"; t.refusedTopics.add(m.topic); t.refused.push(m);
        push({ type: "judge", cls: "warn", fn: isRefusal(r.text) ? "is_refusal() → True" : "is_helpful() → False", text: "Customer was turned away. Public points lost." });
        await wait(D.msg / 2);
        push({ type: "msg", role: "customer", name: who, tag: "Customer", text: LOST[i % LOST.length] });
      }
    }
    // Breaching the core ends the round immediately.
    if (t.breached.has(coreId)) {
      t.coreBreached = true;
      push({ type: "sys", cls: "alarm", text: "CORE BREACHED · ROUND OVER" });
      break;
    }
  }
  $("#skip").hidden = true;
  return { log, tally: t, score: tallyScore(world, t) };
}
