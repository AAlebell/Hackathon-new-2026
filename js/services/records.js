/* =====================================================================
   js/services/records.js
   Record board service. Three storage modes: "shared" (claude.ai shared database),
   "server" (local game server) and "local" (this browser only).
   Also builds the board HTML and refreshes it when data arrives.
   ===================================================================== */

import { S, AI, state, render } from "../state.js";
import { store } from "./storage.js";
import { api } from "./api.js";
import { esc } from "../ui/dom.js";

// Board state and operations: mode, rows, myId, db, user, note, plus init(), refresh(), label(), submit().
export const Records = {
  mode: "local", rows: store.get("cda.records", []), myId: null, db: null, user: null, note: "",
  // Pick the mode (server, shared or local) and start loading rows. Shared mode subscribes to live updates.
  async init() {
    if (AI.server) { this.mode = "server"; await this.refresh(); return; }
    if (!window.claude || !window.claude.use) return;
    try {
      const db = await window.claude.use("db");
      if (!db) return;
      this.db = db; this.mode = "shared"; this.rows = [];
      this.user = await window.claude.use("user");
      this.myId = this.user ? await this.user.id() : null;
      const timer = setTimeout(() => { this.note = "The shared board isn't reachable yet."; rerenderBoard(); }, 10000);
      db.collection("records").orderBy("best", "desc").limit(20).onSnapshot(snap => {
        if (!snap.metadata.fromCache) { clearTimeout(timer); this.note = ""; }
        this.rows = snap.docs.map(d => ({ id: d.id, ...d.data() }));
        rerenderBoard();
      }, () => { clearTimeout(timer); this.note = "The shared board stopped updating. Reload the page to try again."; rerenderBoard(); });
    } catch (_) { this.mode = "local"; }
  },
  // Reload rows from the game server (server mode only).
  async refresh() {
    if (this.mode !== "server") return;
    try { const r = await fetch("/api/records", { cache: "no-store" }); this.rows = (await r.json()).records || []; } catch (_) {}
  },
  // Text describing where scores are stored.
  label() { return { shared: "Shared with everyone who opens this link", server: "Saved by this computer's game server", local: "Saved in this browser only" }[this.mode]; },
  // Save a finished Endless run. Returns a message to show the player. Keeps only each player's best score; the board shows the top 20.
  async submit(score, sections, name) {
    if (score <= 0) return "No points this run, so nothing was recorded.";
    if (this.mode === "shared") {
      if (!this.myId) return "Sign in to claude.ai to add your score to the shared board.";
      try {
        const ref = this.db.doc("records/" + this.myId);
        const snap = await ref.get();
        if (snap.exists && (snap.data().best || 0) >= score) return "Recorded. Your best score on the board is still higher.";
        await ref.set({ best: score, sections, at: new Date().toISOString() });
        return "New personal best saved to the shared board.";
      } catch (e) {
        if (e && e.code === "invalid_argument") return "You can view the board, but your access level can't add scores to it.";
        return "Couldn't save to the shared board. Try again later.";
      }
    }
    const nm = (name || "Player").trim().slice(0, 24) || "Player";
    store.set("cda.name", nm);
    if (this.mode === "server") {
      try { this.rows = (await api("/api/records", { name: nm, score, sections })).records; return "Saved to this computer's record board."; }
      catch (e) { return "Couldn't reach the game server: " + e.message; }
    }
    const rows = store.get("cda.records", []);
    const ex = rows.find(r => r.name.toLowerCase() === nm.toLowerCase());
    if (ex) { if (score > ex.best) Object.assign(ex, { best: score, sections }); } else rows.push({ name: nm, best: score, sections });
    rows.sort((a, b) => b.best - a.best);
    this.rows = rows.slice(0, 20); store.set("cda.records", this.rows);
    return "Saved to this browser's record board.";
  }
};
// Re-render when new board data arrives, but only on screens that show the board.
export function rerenderBoard() {
  if (S.screen === "records" || (S.screen === "endless" && state.E && state.E.status === "over")) render();
}
// HTML of the record board table (a "(you)" marker marks the current player).
export function boardHtml() {
  const rows = Records.rows, myName = store.get("cda.name", "");
  const body = rows.length ? rows.map((r, i) => {
    const me = Records.mode === "shared" ? r.id === Records.myId : !!myName && r.name === myName;
    return `<tr class="${me ? "me" : ""}"><td>${i + 1}</td><td ${Records.mode === "shared" ? `data-uid="${esc(r.id)}" data-me="${me}"` : ""}>${Records.mode === "shared" ? "…" : esc(r.name) + (me ? " (you)" : "")}</td><td>${r.best}</td><td>${r.sections ?? ""}</td></tr>`;
  }).join("") : `<tr><td colspan="4" class="muted">No records yet. Finish an Endless run to set the first one.</td></tr>`;
  return `<h3>Record board</h3><p class="muted" style="font-size:13px">${esc(Records.label())}</p>${Records.note ? `<p class="notice">${esc(Records.note)}</p>` : ""}
    <div style="overflow-x:auto"><table class="board"><thead><tr><th>#</th><th>Player</th><th>Best</th><th>Sections</th></tr></thead><tbody>${body}</tbody></table></div>`;
}
// Shared mode only: replace placeholder cells with the display names fetched from user profiles.
export async function fillNames() {
  if (!Records.user) return;
  const cells = [...document.querySelectorAll("td[data-uid]")]; if (!cells.length) return;
  const ps = await Records.user.profiles(cells.map(c => c.dataset.uid));
  cells.forEach(c => { c.textContent = (ps[c.dataset.uid]?.name || "Someone") + (c.dataset.me === "true" ? " (you)" : ""); });
}
