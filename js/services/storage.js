/* =====================================================================
   js/services/storage.js
   Thin wrapper around localStorage (JSON values, errors ignored) and the saved
   campaign progress. Importing this module restores state.progress and state.speed
   from localStorage, so it must be imported before the first render.
   ===================================================================== */

import { state } from "../state.js";

// store.get(key, default) reads and parses a value; store.set(key, value) stringifies and saves it.
// Both fail silently, for example in private browsing.
export const store = {
  get(k, d) { try { const v = localStorage.getItem(k); return v == null ? d : JSON.parse(v); } catch (_) { return d; } },
  set(k, v) { try { localStorage.setItem(k, JSON.stringify(v)); } catch (_) {} }
};
// Restore saved data into the shared state at load time.
state.progress = store.get("cda.progress.v2", {});
state.speed = store.get("cda.speed", "normal");
// Write state.progress back to localStorage.
export const saveProgress = () => store.set("cda.progress.v2", state.progress);
