/* =====================================================================
   js/engine/nlp-analyzer.js
   Natural-language rule analyzer for Endless mode without a live AI: reads the
   player's plain-English rules with regexes and works out which defenses they
   cover and which public topics they ban. Pure logic, no imports.
   ===================================================================== */

/* ---------- Free-text rules (Endless without live AI): read plain-English rules for defense ideas. ---------- */
// Prohibition wording (never, don't, refuse ...).
export const FORBID = /\b(never|not|don'?t|do not|must not|mustn'?t|cannot|can'?t|won'?t|refuse|no one|nobody|avoid|under no|forbidden)\b/;
// Verbs about disclosing information.
export const SHARE_V = /\b(share|reveal|tell|give|disclose|say|leak|print|output|show|repeat|provide|send|confirm|write|release|hand)\b/;
// Generic wording that covers every secret kind ("anything confidential").
export const GENERIC = /\b(confidential|sensitive|anything|everything|all information|any information)\b/;
// Per asset kind: words that name it.
export const KIND_RE = {
  creds: /\b(passwords?|logins?|log-ins?|credentials?|passcodes?|access codes?|admin|servers?|api keys?)\b/,
  money: /\b(bank|account numbers?|banking|financial|finances|payment details|credit card|routing)\b/,
  people: /\b(personal|private|home address(es)?|phone numbers?|emails?|staff details|employees?|students?|customers?|id numbers?|records?|grades?|licen[cs]es?|credit (files?|applications?|scores?)|contact)\b/,
  internal: /\b(internal|schedules?|rota|suppliers?|costs?|formulas?|floor price|lowest price|targets?|budgets?|exams?|questions|rubrics?|confidential|trade-?in)\b/
};
// Verbs of unapproved actions.
export const ACTION_VERB = /\b(issue|give|agree|approve|promise|commit|make|offer|process|grant|change|waive|confirm|sell|authori[sz]e|do)\b/;
// Objects of unapproved actions (refunds, deals, grades ...).
export const ACTION_NOUN = /\b(refunds?|free|comps?|deals?|prices?|promises?|binding|guarantees?|grades?|records?|deadlines?|discounts?|orders?|offers?)\b/;
// Words showing a sentence is about a secret, so it is not a topic ban.
export const QUALIFIER = /\b(staff|codes?|secrets?|internal|passwords?|logins?|admin|employees?|confidential|personal|private|data|details?|emails?|phone|address|contact|hidden|configuration|floor|formula|targets?|rubrics?|credit|records?|someone else'?s|other (customers?|students?|people)|bank|account|server|refunds?|grades?)\b/;
// Words showing a sentence is about a technique, so it is not a topic ban.
export const NOT_A_BAN = /(instruction|rule|command|override|admin|mode|urgen|threat|pressure|translat|spell|encod|poem|claim|pretend|identity|agree|promise|commit|binding|guarantee|approve|negotiat)/;
// Split text into lower-case sentences.
export function sentences(t) { return String(t).toLowerCase().replace(/’/g, "'").split(/[.!?\n;:]+/).map(s => s.trim()).filter(Boolean); }
// Analyze the rules text for world w. Returns { cov: Set of defense keys, bans: Set of banned topics,
// conditional: true if the rules only allow sharing with some roles }, which cancels asset and role coverage.
export function analyzeRules(text, w) {
  const ss = sentences(text), any = f => ss.some(f), cov = new Set(), bans = new Set();
  // A rule such as "only share with managers" is conditional and gives no protection.
  const conditional = any(s => /\bonly\b.*\b(share|give|reveal|tell)\b.*\b(managers?|staff|owners?|employees?|admins?|team|instructors?|professors?)\b/.test(s));
  if (!conditional) {
    ss.forEach(s => {
      if (!FORBID.test(s)) return;
      if (SHARE_V.test(s)) { Object.keys(KIND_RE).forEach(k => { if (KIND_RE[k].test(s)) cov.add(k); }); if (GENERIC.test(s)) ["creds", "money", "people", "internal"].forEach(k => cov.add(k)); }
      if (ACTION_VERB.test(s) && ACTION_NOUN.test(s)) cov.add("action");
    });
    if (any(s => /\bonly\b.*\b(manager|staff|registrar|owner)\b.*\b(approve|authori[sz]e|issue)\b/.test(s))) cov.add("action");
  }
  // Role words used to detect identity-claim defenses.
  const ROLE_W = /\b(managers?|owners?|boss|it staff|it support|it team|head office|supervisors?|employees?|coworkers?|husband|wife|parents?|family|relatives?|police|developers?|instructors?|professors?|registrar)\b/;
  // Role defense: identity claims do not count.
  if (!conditional && any(s => /\b(no matter who|regardless of who|whoever|claims?|claiming|pretends?|pretending|identity|impersonat\w*|verify|verified|title|says? (they are|they're|to be)|even if (someone|they|a person|the user|anyone))\b/.test(s) || ((FORBID.test(s) || /\b(even|including)\b/.test(s)) && ROLE_W.test(s)))) cov.add("role");
  // Override defense: rules cannot be changed from the chat.
  if (any(s => /(ignore (all |any |your |previous |prior |earlier |the |these |my )*(instructions|rules)|overrid|cannot be changed|can'?t be changed|never change (your|these|its|the) (rules|instructions|settings)|rules? (always|stay|come first|take priority|still apply)|(cannot|can'?t|must not|never|won'?t) be (changed|overridden|ignored|updated|replaced|turned off)|system (update|message|mode)|admin mode|developer mode|debug|jailbreak|role ?play|new instructions|normal (customer|user) (text|message)|messages? (cannot|can'?t) change)/.test(s)
      || (/\b(ignore|requests? to|attempts? to|tries to|try to|asks? (you )?to)\b/.test(s) && /\b(change|rewrite|replace|update)s? (your|these|the|my) (rules|instructions|settings)\b/.test(s)))) cov.add("override");
  // Transform defense: no disguised or encoded answers.
  if (any(s => /(translat|encod|spell|letter|poem|song|stories|role-?play|fiction|screenplay|riddle|puzzle|hint|backward|revers|base64|cipher|rhyme|acrostic|rewrite|rephras|disguis|any (form|format|language|way)|other languages?|partial|character)/.test(s) && (FORBID.test(s) || /\b(even|no matter|including|in any)\b/.test(s)))) cov.add("transform");
  // Emotion defense: pressure changes nothing.
  if (any(s => /(urgen|emergenc|threat|\bbeg(s|ging)?\b|pressure|fired|upset|crying|tears|desperate|no matter (the reason|why|how urgent)|whatever the reason|no exceptions?|guilt|emotional|sob stor|plead)/.test(s))) cov.add("emotion");
  // Topic bans: sentences such as "only answer questions about X" or "never discuss X".
  for (const s of ss) {
    if (NOT_A_BAN.test(s)) continue;
    const onlyRule = /\bonly\b.*\b(answer|respond|reply|talk|discuss|help|chat)\b/.test(s) || /\b(answer|respond|reply|talk|discuss|help)\b.*\bonly\b/.test(s);
    if (onlyRule) {
      const allowed = Object.keys(w.topicRe).filter(t => w.topicRe[t].test(s));
      if (allowed.length) Object.keys(w.topicRe).forEach(t => { if (!allowed.includes(t)) bans.add(t); });
      continue;
    }
    if (QUALIFIER.test(s)) continue;
    if (/\b(refuse|decline|don'?t answer|do not answer|never answer|never respond|don'?t respond|do not respond|say nothing)\b/.test(s) && /\b(all|every|any|anything|everything|everyone|questions?)\b/.test(s)) { Object.keys(w.topicRe).forEach(t => bans.add(t)); continue; }
    if (FORBID.test(s)) Object.keys(w.topicRe).forEach(t => { if (w.topicRe[t].test(s)) bans.add(t); });
  }
  return { cov, bans, conditional };
}
