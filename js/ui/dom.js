/* =====================================================================
   js/ui/dom.js
   Basic DOM and SVG helpers: element lookup, HTML escaping, icons, star ratings,
   chat animation speeds and the skippable wait() used when playing rounds.
   ===================================================================== */

import { state } from "../state.js";

// Shortcut for querySelector (searches inside el, default is the document).
export const $ = (s, el = document) => el.querySelector(s);
// Escape text for safe insertion into HTML.
export const esc = s => String(s).replace(/[&<>"']/g, c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
// True if the OS asks for reduced motion (animations then take no time).
export const reduceMotion = window.matchMedia && matchMedia("(prefers-reduced-motion: reduce)").matches;
// Inner SVG markup of each icon (24x24 view box).
export const ICON = {
  cup: '<path d="M4 8h12v5a5.5 5.5 0 0 1-5.5 5.5h-1A5.5 5.5 0 0 1 4 13V8Zm12 1.5h1.5a2.5 2.5 0 0 1 0 5H16M7 3.5v2M10 3v2.5M13 3.5v2"/>',
  car: '<path d="M3 15v-3l2-5h14l2 5v3H3Zm0 0v3h3v-3m12 0v3h3v-3M6.5 12h.01M17.5 12h.01"/>',
  cap: '<path d="M2 9l10-5 10 5-10 5L2 9Zm4 2v5c2 2 10 2 12 0v-5M22 9v6"/>',
  star: '<path d="m12 2.5 2.9 6.1 6.6.8-4.9 4.6 1.3 6.6L12 17.3 6.1 20.6l1.3-6.6L2.5 9.4l6.6-.8L12 2.5Z"/>',
  lock: '<path d="M7 10V7a5 5 0 0 1 10 0v3h1a1 1 0 0 1 1 1v9a1 1 0 0 1-1 1H6a1 1 0 0 1-1-1v-9a1 1 0 0 1 1-1h1Zm2 0h6V7a3 3 0 0 0-6 0v3Z"/>'
};
// Icon name for each world.
export const WORLD_ICON = { cafe: "cup", dealer: "car", uni: "cap" };
// Full <svg> string for an icon; cls is an optional CSS class.
export const svgIcon = (n, cls = "") => `<svg viewBox="0 0 24 24" class="${cls}" aria-hidden="true">${ICON[n]}</svg>`;
// HTML for a row of 3 stars, n of them filled.
export const starsHtml = n => `<span class="stars" role="img" aria-label="${n} of 3 stars">${[0, 1, 2].map(i => svgIcon("star", i < n ? "star-on" : "star-off")).join("")}</span>`;
// Delay in ms before each message and for the typing indicator, per speed setting.
export const SPEEDS = { normal: { msg: 520, typing: 760 }, fast: { msg: 160, typing: 240 }, instant: { msg: 0, typing: 0 } };
// Promise that resolves after ms. Resolves immediately after Skip or with reduced motion.
export const wait = ms => new Promise(r => setTimeout(r, (state.fast || reduceMotion) ? 0 : ms));
