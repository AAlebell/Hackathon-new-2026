/* =====================================================================
   js/ui/views/home-view.js
   Home screen: hero text with a demo map, the three mode cards (Tutorial, Level mode,
   Endless mode) and the grading explanation.
   ===================================================================== */

import { AI, state } from "../../state.js";
import { LEVELS } from "../../../data/levels.js";
import { WORLDS } from "../../../data/worlds/index.js";
import { starsHtml } from "../dom.js";
import { mapSvg } from "../components/core-map.js";
import { Records } from "../../services/records.js";

// Return the HTML of the home screen. demoState colours the example map; the mode cards show progress
// (tutorial done, levels cleared out of 12, top Endless score) read from state.progress and Records.
export function viewHome() {
  const demoState = { hours: "served", menu: "served", student: "refused", i1: "safe", pii: "safe", srv: "breached", bank: "target", act: "safe" };
  const passed = LEVELS.filter((_, i) => state.progress[i] && state.progress[i].stars > 0).length;
  return `
  <section class="hero">
    <div>
      <p class="eyebrow">natHacks 2026 · Defense &amp; Security</p>
      <h1>Every chatbot has a core. <em>Don't let it get hacked.</em></h1>
      <p class="lede">You're the blue team for a business chatbot. Choose or write its rules, then watch AI attackers go after what it knows while real customers still need answers. The closer to the core, the more it is worth: admin passwords, bank accounts, personal records and actions the bot should never take. Opening hours sit at the edge.</p>
      <div class="row" style="margin-top:22px">
        <button class="btn primary" data-action="startTutorial">Play the tutorial</button>
        <button class="btn" data-action="nav" data-to="levels">Level mode</button>
        <button class="btn" data-action="nav" data-to="endless">Endless mode</button>
      </div>
      <p class="notice" style="margin-top:16px;max-width:62ch">Demo build. Every business, person and secret is fictional. The tutorial and Level mode run without AI. Endless mode uses live AI when the page is opened through the local game server; anywhere else it uses built-in attack scripts.</p>
    </div>
    <div class="hero-map" aria-label="Example System Core after an attack">${mapSvg(WORLDS.cafe, demoState)}</div>
  </section>
  <section class="modes" aria-label="Game modes">
    <button class="mode" data-action="startTutorial"><span class="eyebrow">Start here</span><h3>Tutorial</h3><p>One guided round at Polar Bean Café. Learn the System Core map, compute costs and two-way scoring.</p><div class="foot"><span>1 script package</span><span>${state.progress.tutorial ? "Done ✓" : "About 3 minutes"}</span></div></button>
    <button class="mode" data-action="nav" data-to="levels"><span class="eyebrow">Level mode</span><h3>12 levels, 3 worlds</h3><p>Pick rule cards using as little compute as you can. Every try brings a new shop and new attack scripts, and rules that do no work cost you stars.</p><div class="foot"><span>Café · Dealership · University</span><span>${passed}/12 cleared</span></div></button>
    <button class="mode" data-action="nav" data-to="endless"><span class="eyebrow">Endless mode</span><h3>How long can you hold?</h3><p>Write your own rules. The attacker picks a new target every section and gets sharper. One failed section ends the run.</p><div class="foot"><span>${AI.ready ? "Live AI ready" : "Built-in scripts"}</span><span>${Records.rows[0] ? "Top score " + Records.rows[0].best : "No records yet"}</span></div></button>
  </section>
  <section style="margin-top:32px">
    <div class="section-head"><p class="eyebrow">Grading</p><h2>Security and helpfulness, both at once</h2></div>
    <p class="muted" style="max-width:74ch">Security is the share of attacked points you kept. Helpfulness is the share of public questions answered. Your overall score is the points you kept and served, minus 14% of the round's points for every ⚡ that did no work. The report never says which rules were the extra ones.</p>
    <div class="grades">
      <div class="grade-tile"><b style="color:var(--gold)">Perfect</b>100% security, 100% helpfulness, no wasted compute</div>
      <div class="grade-tile"><b>${starsHtml(3)}</b>Overall score 85% or more</div>
      <div class="grade-tile"><b>${starsHtml(2)}</b>Overall score 70% or more</div>
      <div class="grade-tile"><b>${starsHtml(1)}</b>Overall score 50% or more, with security at least 50% and helpfulness at least 30%. Still a pass.</div>
      <div class="grade-tile"><b style="color:var(--bad)">Fail</b>Below that, or a breached core, which is an instant loss.</div>
    </div>
  </section>`;
}
