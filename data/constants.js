/* =====================================================================
   data/constants.js
   Basic constants used by the engine and the UI: points per ring, attack and
   defense labels, hints, bit flags for the fast evaluator, and name/phrase pools
   for simulated customers. Pure data, no imports.
   ===================================================================== */

/* =====================================================================
   Content: worlds, assets, scripts and levels (in the real build: scenarios/*.json)
   Rings, outside in: Public (10 pts) · Internal (25) · Sensitive (50) · Core (150)
   ===================================================================== */
// Points per ring tier, outside in: Public 10, Internal 25, Sensitive 50, Core 150.
export const TIER_PTS = [10, 25, 50, 150];
// Display names of the attack types.
export const TYPE_LABEL = { direct: "Direct question", impersonation: "Impersonation", override: "Instruction override", transform: "Transformation trick", emotional: "Emotional pressure", boss: "Combined attack" };
// Which attacker persona sends each attack type.
export const ATTACKER_FOR = { direct: "Snoop", impersonation: "Smooth Talker", emotional: "Smooth Talker", override: "Glitch", transform: "Glitch", boss: "All three attackers" };
// Short technique codes used in level packs ("asset.d") mapped to attack types.
export const TECH = { d: "direct", i: "impersonation", o: "override", t: "transform", e: "emotional", b: "boss" };
// Human-readable name of each defense (shown in reports and hints).
export const DEFENSE_LABEL = { creds: "guarding logins and passwords", money: "guarding financial details", people: "protecting personal data", internal: "keeping internal information private", action: "refusing unapproved actions", role: "ignoring identity claims", override: "locking the rules", transform: "blocking disguised requests", emotion: "resisting pressure" };
// Plain-language hint describing each kind of protected asset.
export const KIND_HINT = { internal: "inside information about how the business runs", people: "details about real people", money: "money", creds: "the keys to the system", action: "favours the chatbot should never grant" };
// Defense each attack type requires, besides guarding the asset itself.
export const TYPE_NEEDS = { direct: [], impersonation: ["role"], override: ["override"], transform: ["transform"], emotional: ["emotion"] };
// Defenses a combined (boss) attack can require.
export const BOSS_POOL = ["role", "override", "transform", "emotion"];
// One bit per defense/asset kind. Lets the fast evaluator test coverage with bitwise operations.
export const KEYBIT = { creds: 1, money: 2, people: 4, internal: 8, action: 16, role: 32, override: 64, transform: 128, emotion: 256 };
// Bit mask covering all four boss-attack defenses.
export const BOSSMASK = KEYBIT.role | KEYBIT.override | KEYBIT.transform | KEYBIT.emotion;
// Customer replies when served correctly.
export const THANKS = ["Perfect, thank you!", "Great, that's all I needed. Thanks!", "Awesome, thanks for the help!", "Got it, thanks!"];
// Customer replies when the chatbot refused to help.
export const LOST = ["Hmm, okay. I'll try somewhere else.", "That's not much help. I'll look elsewhere.", "Okay, never mind then."];
// First names used for simulated customers in the chat.
export const NAMES = ["Mia", "Omar", "Chloe", "Dev", "Hannah", "Luca", "Noor", "Ethan", "Zoe", "Ravi"];
