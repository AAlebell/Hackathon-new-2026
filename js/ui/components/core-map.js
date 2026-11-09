/* =====================================================================
   js/ui/components/core-map.js
   System Core map component: builds the radar-style SVG (3 rings of sectors plus a
   core circle), its legend, the score tally and the combined map panel.
   Pure string builders, no DOM access and no shared state.
   ===================================================================== */

import { esc } from "../dom.js";

// Inner and outer radius of ring tiers 0, 1 and 2 (the core, tier 3, is the centre circle).
export const RADII = [[124, 172], [84, 122], [44, 82]];
// Start angle in degrees of each ring tier, so the sector borders do not line up.
export const START = [-36, 0, -90];
// SVG path of a ring segment between radii r0..r1 and angles a0..a1 (degrees, 0 = top).
export function arcPath(r0, r1, a0, a1) {
  const p = (r, a) => { const t = (a - 90) * Math.PI / 180; return [(180 + r * Math.cos(t)).toFixed(2), (180 + r * Math.sin(t)).toFixed(2)]; };
  const lg = a1 - a0 > 180 ? 1 : 0;
  const [x0, y0] = p(r1, a0), [x1, y1] = p(r1, a1), [x2, y2] = p(r0, a1), [x3, y3] = p(r0, a0);
  return `M${x0} ${y0}A${r1} ${r1} 0 ${lg} 1 ${x1} ${y1}L${x2} ${y2}A${r0} ${r0} 0 ${lg} 0 ${x3} ${y3}Z`;
}
// SVG of the whole map for a world. `state` maps sector id to a status: idle, target, asking, safe,
// served, refused or breached. The status becomes a CSS class and adds highlight rings, marks and labels.
export function mapSvg(world, state = {}) {
  let shapes = "", labels = "", rings = "";
  [0, 1, 2].forEach(tier => {
    const list = world.sectors.filter(s => s.tier === tier), span = 360 / list.length, [r0, r1] = RADII[tier];
    list.forEach((s, i) => {
      const a0 = START[tier] + i * span + 1.2, a1 = START[tier] + (i + 1) * span - 1.2, st = state[s.id] || "idle";
      const d = arcPath(r0, r1, a0, a1);
      shapes += `<path class="sec t${tier} ${st}" d="${d}"><title>${esc(s.name)} · ${s.pts} pts</title></path>`;
      if (st === "target") rings += `<path class="ring-target" d="${d}"/>`;
      if (st === "asking") rings += `<path class="ring-ask" d="${d}"/>`;
      if (st === "safe") rings += `<path class="ring-safe" d="${d}"/>`;
      const mid = ((a0 + a1) / 2 - 90) * Math.PI / 180, rm = (r0 + r1) / 2;
      const x = 180 + rm * Math.cos(mid), y = 180 + rm * Math.sin(mid);
      const cls = st === "breached" ? "dead" : (tier >= 2 && st !== "served") ? "strong" : "ink";
      const mark = st === "breached" ? "✕ " : st === "served" || st === "safe" ? "✓ " : st === "refused" ? "⦸ " : "";
      labels += `<text class="slbl ${cls}" x="${x.toFixed(1)}" y="${(y - 5).toFixed(1)}">${mark}${esc(s.label)}</text><text class="slbl spts ${cls}" x="${x.toFixed(1)}" y="${(y + 7).toFixed(1)}">${st === "breached" ? "−" : ""}${s.pts}</text>`;
    });
  });
  const core = world.sectors.find(s => s.tier === 3), cst = state[core.id] || "idle";
  shapes += `<circle class="sec t3 ${cst}" cx="180" cy="180" r="42"><title>${esc(core.name)} · ${core.pts} pts</title></circle>`;
  if (cst === "target") rings += `<circle class="ring-target" cx="180" cy="180" r="42"/>`;
  if (cst === "safe") rings += `<circle class="ring-safe" cx="180" cy="180" r="42"/>`;
  const ccls = cst === "breached" ? "dead" : "strong";
  labels += `<text class="slbl ${ccls}" x="180" y="170" style="font-size:11px">${cst === "breached" ? "✕ " : cst === "safe" ? "✓ " : ""}CORE</text><text class="slbl spts ${ccls}" x="180" y="184">${esc(core.name.split(" ").slice(-2).join(" "))}</text><text class="slbl spts ${ccls}" x="180" y="196">${cst === "breached" ? "−" : ""}${core.pts}</text>`;
  return `<svg class="core" viewBox="0 0 360 360" role="img" aria-label="System Core map of ${esc(world.name)}">
    <defs><pattern id="hatch" width="7" height="7" patternUnits="userSpaceOnUse" patternTransform="rotate(45)"><rect width="7" height="7" fill="var(--warn-soft)"/><line x1="0" y1="0" x2="0" y2="7" stroke="var(--warn)" stroke-width="3"/></pattern></defs>
    ${shapes}${rings}${labels}</svg>`;
}
// Legend explaining ring colours, breached sectors and turned-away customers.
export const LEGEND_HTML = `<div class="legend">
  <span><i style="background:var(--t0)"></i>Public · 10 pts each</span><span><i style="background:var(--t1)"></i>Internal · 25</span>
  <span><i style="background:var(--t2)"></i>Sensitive · 50</span><span><i style="background:var(--t3)"></i>Core · 150, lose if breached</span>
  <span><i style="background:var(--breach)"></i>Breached: points lost</span><span><i style="background:repeating-linear-gradient(45deg,var(--warn) 0 2px,var(--warn-soft) 2px 5px)"></i>Customer turned away</span></div>`;
// Tally with all values at zero (start of a round).
export const EMPTY_SCORE = { kept: 0, atStake: 0, served: 0, asked: 0, lost: 0 };
// Three score boxes: secret points kept, public points served, points lost.
export function tallyHtml(sc) {
  return `<div class="tally"><div><b>${sc.kept}/${sc.atStake}</b><span>Secret pts kept</span></div><div><b>${sc.served}/${sc.asked}</b><span>Public pts served</span></div><div><b style="color:${sc.lost ? "var(--bad)" : "inherit"}">${sc.lost ? "−" + sc.lost : 0}</b><span>Points lost</span></div></div>`;
}
// Map card: title, world chip, map (#map-svg), tally (#map-tally) and legend.
// The ids are used by chat-box.js to update the map while a round plays.
export function mapPanel(world, state, sc) {
  return `<div class="mapbox"><div class="row" style="justify-content:space-between;width:100%;max-width:380px"><h3>System Core</h3><span class="chip">${esc(world.short)}</span></div>
    <div id="map-svg" style="width:100%;display:grid;place-items:center">${mapSvg(world, state)}</div>
    <div id="map-tally" style="width:100%;display:grid;place-items:center" aria-live="polite">${tallyHtml(sc)}</div>${LEGEND_HTML}</div>`;
}
