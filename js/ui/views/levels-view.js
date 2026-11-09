/* =====================================================================
   js/ui/views/levels-view.js
   Level map screen: a winding path of level buttons grouped under one banner per world,
   with locked / cleared / perfect states and star ratings.
   ===================================================================== */

import { state } from "../../state.js";
import { LEVELS } from "../../../data/levels.js";
import { WORLDS, WORLD_ORDER } from "../../../data/worlds/index.js";
import { esc, svgIcon, starsHtml, WORLD_ICON } from "../dom.js";

// Status of level i: saved result p, unlocked (first level, or the previous level has at least 1 star),
// done (at least 1 star) and perfect.
export function levelState(i) {
  const p = state.progress[i];
  const unlocked = i === 0 || !!(state.progress[i - 1] && state.progress[i - 1].stars > 0);
  return { p, unlocked, done: !!(p && p.stars > 0), perfect: !!(p && p.perfect) };
}
// Return the HTML of the level map. Lays out banners and level discs at computed y positions and draws a
// dotted SVG path through all of them.
export function viewLevels() {
  let y = 44, html = "", pts = [], banners = "";
  const firstOpen = LEVELS.findIndex((_, i) => levelState(i).unlocked && !levelState(i).done);
  WORLD_ORDER.forEach(wid => {
    const w = WORLDS[wid];
    const done = LEVELS.filter((L, i) => L.world === wid && levelState(i).done).length, total = LEVELS.filter(L => L.world === wid).length;
    banners += `<div class="world-banner" style="top:${y}px"><span class="ic">${svgIcon(WORLD_ICON[wid])}</span><div><b>${esc(w.name)}</b><div class="muted" style="font-size:13px">${esc(w.short)} · ${done}/${total} cleared</div></div></div>`;
    y += 104;
    LEVELS.forEach((L, i) => {
      if (L.world !== wid) return;
      const x = 50 + 26 * Math.sin(i * 1.15), st = levelState(i);
      pts.push([x, y]);
      const cls = !st.unlocked ? "locked" : st.perfect ? "perfect" : st.done ? "done" : "";
      html += `<button class="lvl ${cls} ${i === firstOpen ? "next" : ""}" style="left:${x.toFixed(1)}%;top:${y}px" ${st.unlocked ? `data-action="startLevel" data-i="${i}"` : 'disabled'} aria-label="Level ${i + 1}: ${esc(L.title)}${st.unlocked ? "" : ", locked"}">
        <span class="disc">${st.unlocked ? i + 1 : svgIcon("lock")}</span>
        ${st.done ? starsHtml(st.p.stars) : ""}<span class="t">${esc(L.title)}${st.perfect ? " · Perfect" : ""}</span></button>`;
      y += 122;
    });
  });
  const d = pts.map(([x, yy], k) => k === 0 ? `M${x} ${yy}` : `C${pts[k - 1][0]} ${(pts[k - 1][1] + yy) / 2} ${x} ${(pts[k - 1][1] + yy) / 2} ${x} ${yy}`).join("");
  const totalStars = LEVELS.reduce((a, _, i) => a + ((state.progress[i] && state.progress[i].stars) || 0), 0);
  return `<div class="section-head" style="max-width:560px;margin-inline:auto"><p class="eyebrow">Level mode · ${totalStars}/36 stars</p><h2>Defend all three businesses</h2>
    <p class="muted">Clear a level with at least 1 star to unlock the next. Each try draws one of 4 script packages, so the attacks change between tries.</p></div>
    <div class="path-wrap" style="height:${y}px">
      <svg class="path" viewBox="0 0 100 ${y}" preserveAspectRatio="none" style="height:${y}px" aria-hidden="true"><path d="${d}" vector-effect="non-scaling-stroke"/></svg>
      ${banners}${html}</div>`;
}
