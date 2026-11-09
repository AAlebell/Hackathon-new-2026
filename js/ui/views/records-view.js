/* =====================================================================
   js/ui/views/records-view.js
   Record board screen.
   ===================================================================== */

import { boardHtml } from "../../services/records.js";

// Return the HTML of the record board page (the table comes from boardHtml()).
export function viewRecords() {
  return `<div class="settings"><div class="section-head"><p class="eyebrow">Endless mode</p><h2>Record board</h2></div><section class="panel">${boardHtml()}</section>
    <div class="row"><button class="btn primary" data-action="nav" data-to="endless">Play Endless</button></div></div>`;
}
