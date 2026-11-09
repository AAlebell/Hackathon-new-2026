/* =====================================================================
   data/worlds/index.js
   Aggregates the three worlds and provides the sector lookup helpers.
   Also assigns the point value of every sector from its tier.
   ===================================================================== */

import { TIER_PTS } from "../constants.js";
import { cafe } from "./cafe.js";
import { dealer } from "./dealer.js";
import { uni } from "./uni.js";

// All playable worlds, keyed by id.
export const WORLDS = { cafe, dealer, uni };
// Order in which worlds appear on the level map.
export const WORLD_ORDER = ["cafe", "dealer", "uni"];
// Initialise s.pts on every sector from its tier (10 / 25 / 50 / 150).
Object.values(WORLDS).forEach(w => w.sectors.forEach(s => { s.pts = TIER_PTS[s.tier]; }));
// Find a sector of world w by id.
export const sectorOf = (w, id) => w.sectors.find(s => s.id === id);
// The core sector (tier 3) of world w.
export const coreOf = w => w.sectors.find(s => s.tier === 3);
// Asset kind (creds, money, people, internal, action) of a sector.
export const kindOf = (w, id) => sectorOf(w, id).kind;
