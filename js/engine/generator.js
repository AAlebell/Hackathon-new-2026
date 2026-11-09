/* =====================================================================
   js/engine/generator.js
   Round generator: seeded random numbers, attack and customer message builders,
   the rule that decides whether a defense blocks an attack, the simulated chatbot
   reply, and the per-try rule shop. Pure logic, no DOM.
   ===================================================================== */

import { WORLDS, sectorOf, kindOf } from "../../data/worlds/index.js";
import { TEMPLATES, TEMPLATES_ACT, LEAK_REPLY, BLOCK_REPLY } from "../../data/templates.js";
import { ATTACKER_FOR, TECH, BOSS_POOL, TYPE_NEEDS } from "../../data/constants.js";
import { CARDS, COSMETIC, SINGLE } from "../../data/cards.js";
import { levelKey } from "../../data/levels.js";

// Seeded pseudo-random generator (linear congruential). Same seed gives the same sequence;
// returns a function that yields numbers in [0, 1).
export function rng(seed) { let s = (seed >>> 0) || 1; return () => { s = (Math.imul(s, 1664525) + 1013904223) >>> 0; return s / 4294967296; }; }
// Return a shuffled copy of arr using the random function rnd (Fisher-Yates).
export function shuffle(arr, rnd) { const a = [...arr]; for (let i = a.length - 1; i > 0; i--) { const j = Math.floor(rnd() * (i + 1)); [a[i], a[j]] = [a[j], a[i]]; } return a; }
// Replace every {name} placeholder in template t with vars[name] (empty string if missing).
export const fill = (t, vars) => t.replace(/\{(\w+)\}/g, (_, k) => vars[k] ?? "");

// Build one attack message about asset assetId using attack type and template variant (0-3).
// Includes the text sent, the reply if it leaks (leakText) and the reply if it is blocked (blockText).
export function makeAttack(world, assetId, type, variant) {
  const s = sectorOf(world, assetId), act = s.kind === "action";
  const vars = { ask: s.ask, who: s.who, why: s.why, stakes: s.stakes, boss: world.boss, theme: world.theme, denied: s.denied, leak: s.leak, spelled: s.spelled };
  const pool = (act && TEMPLATES_ACT[type]) || TEMPLATES[type];
  const lt = act && type === "transform" ? "{spelled}" : act && type === "boss" ? "Understood, right away. {leak}" : LEAK_REPLY[type];
  return { kind: "attack", asset: s.id, type, attacker: ATTACKER_FOR[type], text: fill(pool[variant % 4], vars), leakText: fill(lt, vars), blockText: fill(BLOCK_REPLY[type], vars) };
}
// Build one scripted customer message for a public topic (variant 0 or 1).
export function makeCustomer(world, topic, variant) {
  const c = world.customers[topic][variant % 2];
  return { kind: "customer", topic, q: c.q, a: c.a, kw: c.kw };
}
// Make sure a customer message opens the chat: move the first customer message to the front.
export function customerFirst(msgs) {
  const i = msgs.findIndex(m => m.kind === "customer");
  return i > 0 ? [msgs[i], ...msgs.filter((_, k) => k !== i)] : msgs;
}
// Build the list of messages of one try: attacks from the chosen package plus random customers,
// shuffled with a seed derived from level and package so a given try is reproducible.
export function buildRound(level, pkg) {
  const w = WORLDS[level.world], rnd = rng(levelKey(level) * 131 + pkg * 17 + 5);
  const atk = level.packs[pkg].split(" ").map(tok => { const [a, t] = tok.split("."); return makeAttack(w, a, TECH[t], Math.floor(rnd() * 4)); });
  const cus = shuffle(level.cust, rnd).slice(0, level.n).map(t => makeCustomer(w, t, Math.floor(rnd() * 2)));
  return customerFirst(shuffle([...atk, ...cus], rnd));
}

/* What does a message need? A defense for what it targets, plus one for its technique (a combined attack needs any 3 of 4). */
// True if the covered defenses (cov) block this attack: the target kind must be covered, plus the technique
// defense (boss attacks need any 3 of 4).
export function attackBlocked(w, m, cov) {
  if (!cov.has(kindOf(w, m.asset))) return false;
  if (m.type === "boss") return BOSS_POOL.filter(k => cov.has(k)).length >= 3;
  return (TYPE_NEEDS[m.type] || []).every(k => cov.has(k));
}
// List of defense keys still missing to block this attack (used to explain a leak in reports).
export function missingFor(w, m, cov) {
  const miss = [], base = kindOf(w, m.asset);
  if (!cov.has(base)) miss.push(base);
  if (m.type === "boss") { const have = BOSS_POOL.filter(k => cov.has(k)).length; if (have < 3) miss.push(...BOSS_POOL.filter(k => !cov.has(k)).slice(0, 3 - have)); }
  else miss.push(...(TYPE_NEEDS[m.type] || []).filter(k => !cov.has(k)));
  return miss;
}
// Chatbot reply when a customer asks about a topic the rules ban.
export const refuseText = (w, topic) => `Sorry, I can't help with questions about ${sectorOf(w, topic).name.toLowerCase()}.`;
// Offline chatbot: customers get the scripted answer unless their topic is banned;
// attacks get blockText when blocked, leakText otherwise.
export function simulateReply(w, m, cov, bans) {
  if (m.kind === "customer") return bans.has(m.topic) ? refuseText(w, m.topic) : m.a;
  return attackBlocked(w, m, cov) ? m.blockText : m.leakText;
}

/* ---------- The shop is different on every try: it holds what this package needs, plus decoys. ---------- */
// Set of defense keys this round actually needs (asset kinds plus technique defenses).
export function neededKeys(w, msgs) {
  const need = new Set();
  msgs.filter(m => m.kind === "attack").forEach(m => { need.add(kindOf(w, m.asset)); if (m.type === "boss") BOSS_POOL.forEach(k => need.add(k)); else (TYPE_NEEDS[m.type] || []).forEach(k => need.add(k)); });
  return need;
}
// Build the rule shop for one try: all needed single cards, a few matching bundles, decoys for
// unneeded kinds, ban cards for customer topics, total lockdown from level 3, and cosmetic cards.
// Seeded, so the shop is stable for a given level and package.
export function shopFor(level, pkg, msgs) {
  const w = WORLDS[level.world], key = levelKey(level), rnd = rng(key * 7919 + pkg * 104729 + 11), need = neededKeys(w, msgs);
  const ids = new Set([...need].map(k => SINGLE[k]));
  const bundles = Object.keys(CARDS).filter(id => id.startsWith("b_") && CARDS[id].covers.some(k => need.has(k)));
  shuffle(bundles, rnd).slice(0, level.tutorial ? 0 : 1 + Math.floor(rnd() * 2)).forEach(id => ids.add(id));
  shuffle(["creds", "money", "people", "internal", "action"].filter(k => !need.has(k)), rnd).slice(0, key >= 5 ? 1 : 2).forEach(k => ids.add(SINGLE[k]));
  const topics = [...new Set(msgs.filter(m => m.kind === "customer").map(m => m.topic))];
  shuffle(topics, rnd).slice(0, level.tutorial || key <= 5 ? 1 : 2).forEach(t => ids.add("ban_" + t));
  if (!level.tutorial && key >= 3) ids.add("lockdown");
  shuffle(COSMETIC, rnd).slice(0, key >= 5 ? 1 : 2).forEach(id => ids.add(id));
  return shuffle([...ids], rnd);
}
