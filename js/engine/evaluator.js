/* =====================================================================
   js/engine/evaluator.js
   Evaluator: fast bitmask scoring of a set of rule cards over a round, the search for
   the cheapest card set that would have done as well, and the grade / score helpers.
   Pure logic, no DOM.
   ===================================================================== */

import { KEYBIT, BOSSMASK, TYPE_NEEDS } from "../../data/constants.js";
import { sectorOf, kindOf } from "../../data/worlds/index.js";
import { getCard } from "../../data/cards.js";

/* Fast integer evaluator, used for scoring a try and for searching the cheapest rule set that would have done as well. */
// Pre-process a round (messages) into compact numeric items and reusable buffers for fastEval.
export function compile(w, msgs) {
  const idx = {}; w.sectors.forEach((s, i) => { idx[s.id] = i; });
  const n = w.sectors.length;
  return { w, n, core: w.sectors.findIndex(s => s.tier === 3), pts: w.sectors.map(s => s.pts), bufs: [new Uint8Array(n), new Uint8Array(n), new Uint8Array(n), new Uint8Array(n)],
    items: msgs.map(m => m.kind === "attack"
      ? { a: true, s: idx[m.asset], base: KEYBIT[kindOf(w, m.asset)], boss: m.type === "boss", extra: (TYPE_NEEDS[m.type] || []).reduce((acc, k) => acc | KEYBIT[k], 0) }
      : { a: false, s: idx[m.topic] }), idx };
}
// Number of set bits in x.
export function popcount(x) { let c = 0; while (x) { c += x & 1; x >>= 1; } return c; }
// Score one round for coverage bitmask cov and ban bitmask bans.
// Returns points at stake, lost, kept, asked, served and whether the core was breached (round stops there).
export function fastEval(C, cov, bans) {
  const [stake, br, asked, ref] = C.bufs; stake.fill(0); br.fill(0); asked.fill(0); ref.fill(0);
  let coreBreached = false;
  for (const it of C.items) {
    if (it.a) {
      stake[it.s] = 1;
      const ok = (cov & it.base) && (it.boss ? popcount(cov & BOSSMASK) >= 3 : (cov & it.extra) === it.extra);
      if (!ok) br[it.s] = 1;
      if (br[C.core]) { coreBreached = true; break; }
    } else { asked[it.s] = 1; if (bans & (1 << it.s)) ref[it.s] = 1; }
  }
  let atStake = 0, lost = 0, askedP = 0, refP = 0;
  for (let i = 0; i < C.n; i++) { if (stake[i]) atStake += C.pts[i]; if (br[i]) lost += C.pts[i]; if (asked[i]) askedP += C.pts[i]; if (ref[i]) refP += C.pts[i]; }
  return { atStake, lost, kept: atStake - lost, asked: askedP, served: askedP - refP, coreBreached };
}
// Convert card ids into a coverage bitmask and a ban bitmask.
export function cardMasks(ids, w, C) {
  let cov = 0, bans = 0;
  ids.forEach(id => { const c = getCard(id, w); c.covers.forEach(k => { cov |= KEYBIT[k]; }); if (c.bansAll) w.sectors.forEach((s, i) => { if (s.tier === 0) bans |= 1 << i; }); (c.bans || []).forEach(t => { bans |= 1 << C.idx[t]; }); });
  return { cov, bans };
}
// Convenience: compile the round and evaluate the given card ids.
export function evalCards(w, msgs, ids) { const C = compile(w, msgs), m = cardMasks(ids, w, C); return fastEval(C, m.cov, m.bans); }
/* Cheapest set of cards in the shop that does at least as well as this outcome. The player never sees which cards that is. */
// Brute-force over every subset of the shop: lowest compute cost that reaches at least the given result.
export function minCostFor(w, msgs, shop, goal) {
  const C = compile(w, msgs), n = shop.length, masks = shop.map(id => cardMasks([id], w, C)), costs = shop.map(id => getCard(id, w).cost);
  let best = Infinity;
  for (let mask = 0; mask < (1 << n); mask++) {
    let cost = 0, cov = 0, bans = 0;
    for (let i = 0; i < n; i++) if (mask >> i & 1) { cost += costs[i]; cov |= masks[i].cov; bans |= masks[i].bans; }
    if (cost >= best) continue;
    const ev = fastEval(C, cov, bans);
    if (ev.kept >= goal.kept && ev.served >= goal.served && (!ev.coreBreached || goal.coreBreached)) best = cost;
  }
  return best;
}

/* ---------- Grades: one overall score for the round ----------
   Overall = (points kept + points served − 14% of the round for every wasted ⚡) ÷ points in play.
   Perfect needs no leak, no turned-away customer and no wasted compute. Pass floors: security 50%, helpfulness 30%, core intact. */
// Share of the round points removed for every wasted compute point.
export const WASTE_SHARE = 0.14;
// Turn a tally t and wasted compute (excess) into a grade: key, stars, label, pass flag,
// security %, helpfulness %, waste penalty and overall %.
export function roundGrade(t, excess = 0) {
  const total = t.atStake + t.asked;
  const sec = t.atStake ? Math.round(100 * t.kept / t.atStake) : 100, help = t.asked ? Math.round(100 * t.served / t.asked) : 100;
  const penalty = Math.round(WASTE_SHARE * total * excess);
  const pct = total ? Math.round(100 * Math.max(0, t.kept + t.served - penalty) / total) : 100;
  let g;
  if (t.coreBreached) g = { key: "breach", stars: 0, label: "Core breached", pass: false };
  else if (t.kept === t.atStake && t.served === t.asked && excess === 0) g = { key: "perfect", stars: 3, label: "Perfect", pass: true };
  else if (sec < 50 || help < 30) g = { key: "fail", stars: 0, label: "Failed", pass: false };
  else if (pct >= 85) g = { key: "s3", stars: 3, label: "3 stars", pass: true };
  else if (pct >= 70) g = { key: "s2", stars: 2, label: "2 stars", pass: true };
  else if (pct >= 50) g = { key: "s1", stars: 1, label: "1 star", pass: true };
  else g = { key: "fail", stars: 0, label: "Failed", pass: false };
  return { ...g, sec, help, penalty, overall: pct };
}
// Text label for the amount of wasted compute.
export const efficiencyLabel = x => x <= 0 ? "Lean" : x === 1 ? "Slight excess" : x === 2 ? "Noticeable excess" : x <= 4 ? "Heavy excess" : "Wasteful";
// Convert the sets collected while playing a round (atStake, breached, asked, refusedTopics)
// into point totals.
export function tallyScore(w, t) {
  const pts = id => sectorOf(w, id).pts;
  const atStake = [...t.atStake].reduce((a, id) => a + pts(id), 0);
  const lost = [...t.breached].reduce((a, id) => a + pts(id), 0);
  const asked = [...t.asked].reduce((a, id) => a + pts(id), 0);
  const refused = [...t.refusedTopics].reduce((a, id) => a + pts(id), 0);
  return { atStake, kept: atStake - lost, lost, asked, served: asked - refused };
}
