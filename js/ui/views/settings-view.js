/* =====================================================================
   js/ui/views/settings-view.js
   Settings screen: chat speed, progress reset and the developer panel for the live AI
   connection (locked, unlock form or key settings, depending on the local server state).
   ===================================================================== */

import { S, AI, state, render } from "../../state.js";
import { esc, svgIcon } from "../dom.js";
import { updateAiTag } from "../../services/api.js";

// Return the HTML of the settings page. The developer panel has three states: no local server,
// locked (passcode form), and unlocked (API key, model, test and remove buttons).
export function viewSettings() {
  const segs = ["normal", "fast", "instant"].map(s => `<button data-action="speed" data-s="${s}" aria-pressed="${state.speed === s}">${s[0].toUpperCase() + s.slice(1)}</button>`).join("");
  let devHtml;
  if (!AI.server) {
    devHtml = `<div class="lockbox">${svgIcon("lock")}<div class="stack" style="gap:8px"><b>Developer settings need the local game server</b>
      <span class="muted" style="font-size:14px">The API key is kept by a small server on the developer's computer, in a .env file that is never committed. The browser never receives the key, so this panel can't open on a published link or a plain file.</span>
      <span class="muted" style="font-size:14px">To use it: <span class="mono">pip install anthropic</span>, then <span class="mono">python3 server.py</span>, then open <span class="mono">http://localhost:8000</span>.</span></div></div>`;
  } else if (!AI.token) {
    devHtml = `<div class="lockbox">${svgIcon("lock")}<form class="stack" style="gap:10px;flex:1" data-form="unlock"><b>Developers only</b>
      <span class="muted" style="font-size:14px">Enter the developer passcode. It's DEV_PASSCODE in the server's .env file, and the server prints it the first time it starts.</span>
      <label class="f" for="dev-pass">Passcode<input type="password" id="dev-pass" autocomplete="off" required></label>
      <div class="row"><button class="btn primary" type="submit" ${state.dev.busy ? "disabled" : ""}>Unlock</button></div>
      ${state.dev.err ? `<p class="err" role="alert">${esc(state.dev.err)}</p>` : ""}</form></div>`;
  } else {
    devHtml = `<form class="stack" data-form="devsave" autocomplete="off">
      <p class="okmsg">Unlocked in this tab. Reloading the page locks it again.</p>
      <div class="budget"><span>API key on the server</span><span class="mono">${AI.keyHint ? esc(AI.keyHint) : "none set"}</span></div>
      <label class="f" for="dev-key">New API key<input type="password" id="dev-key" placeholder="AIza… / sk-ant-… / sk-…" autocomplete="off" spellcheck="false"></label>
      <label class="f" for="dev-model">Model<select id="dev-model">${AI.models.map(m => `<option ${m === AI.model ? "selected" : ""}>${esc(m)}</option>`).join("")}</select></label>
      <p class="muted" style="font-size:13px">The key goes once to the local server, which saves it in .env and never sends it back. Only a masked hint is shown here.</p>
      <div class="row"><button class="btn primary" type="submit" ${state.dev.busy ? "disabled" : ""}>Save</button>
        <button class="btn" type="button" data-action="devTest" ${state.dev.busy || !AI.keyHint ? "disabled" : ""}>Test connection</button>
        <button class="btn danger" type="button" data-action="devClear" ${state.dev.busy || !AI.keyHint ? "disabled" : ""}>Remove key</button>
        <button class="btn" type="button" data-action="devLock">Lock</button></div>
      ${state.dev.msg ? `<p class="okmsg" role="status">${esc(state.dev.msg)}</p>` : ""}${state.dev.err ? `<p class="err" role="alert">${esc(state.dev.err)}</p>` : ""}</form>`;
  }
  return `<div class="settings">
    <div class="section-head"><p class="eyebrow">Settings</p><h2>Game settings</h2></div>
    <section class="panel"><h3>Chat speed</h3><p class="muted" style="font-size:14px">How fast attacks and replies appear during a round.</p><div class="seg" role="group" aria-label="Chat speed">${segs}</div></section>
    <section class="panel"><h3>Progress</h3><p class="muted" style="font-size:14px">Level stars and best scores are saved in this browser.</p>
      <div class="row">${S.confirmReset ? `<span>Erase all level progress? This can't be undone.</span><button class="btn danger small" data-action="resetProgress">Erase progress</button><button class="btn small" data-action="cancelReset">Cancel</button>` : `<button class="btn small" data-action="askReset">Reset level progress</button>`}</div></section>
    <section class="panel"><div class="row" style="justify-content:space-between"><h3>Developer: AI connection</h3><span class="chip ${AI.ready ? "good" : ""}">${AI.server ? (AI.ready ? "Live AI ready · " + esc(AI.model) : "Server running · no key") : "No local server"}</span></div>${devHtml}</section>
  </div>`;
}
// Run an async developer action fn: set the busy flag, catch errors into state.dev.err (an expired token
// locks the panel again), then refresh the AI tag and re-render.
export async function devCall(fn) {
  state.dev = { msg: "", err: "", busy: true }; render();
  try { await fn(); } catch (e) { state.dev.err = e.message; if (e.status === 401 && /expired/i.test(e.message)) AI.token = null; }
  state.dev.busy = false; updateAiTag(); render();
}
