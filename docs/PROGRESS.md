# Progress

Contract: docs/MASTER_PROMPT.md section 4.

## Phases
- [x] Phase 0 (A) Skeleton
- [x] Phase 1 (A) engine/ai.py
- [x] Phase 2 (A) Loader and tutorial level
- [x] Phase 3 (A) Level engine
- [x] Phase 4 (A) Grading
- [x] Phase 5 (A) Save and load
- [x] Phase 6 (B) Interface part 1
- [x] Phase 7 (B) Playback and results
- [x] Phase 8 (B) Tutorial guide
- [x] Phase 9 (A) More levels and balance test
- [x] Phase 10 (A) Endless engine
- [x] Phase 11 (B) Endless interface
- [x] Phase 12 Storage (part A done, part B done)
- [x] Phase 13 Final checks (part A done, part B done)

## Decisions
- Person A works on one branch, dong/auto-run, with one pull request for phases 0 to 13A (user request).
- CLAUDE.md contract and scenario shape sections now point to docs/MASTER_PROMPT.md section 4.
- test_engine.py now just runs tests/run_all.py.

- call_ai reads USE_FAKE_AI at call time (not import time), so tests can switch it per process.

- scenarios/cafe.json is a copy of docs/cafe.json (old prototype format removed). The loader also accepts attack type "combined", used by the content file.
- The old app.py, engine/easy.py and engine/rounds.py no longer work with the new cafe.json. Expected, Phase 6 (James) rewrites app.py; Phases 3 and 10 replace the old engine files.

- security and helpfulness totals count only the zones attacked or asked about in the played package (same as docs/check_cafe_design.py). Zones nobody touched stay safe on the map but add no points.
- Event steps start at 1, like docs/sample_results.json.
- engine/easy.py deleted in Phase 3, superseded by engine/level.py.

- Grading: "perfect" also needs no length penalty (written rules up to 400 characters). Scores and percentages are rounded to whole numbers.

- import_game accepts "events" at the top level of the record or inside a nested "result" dict.

- Phase 9: the optional level_3 and level_4 were not added (content was frozen in docs/cafe.json). tests/test_balance.py checks every level of every scenario.

- Endless: a secret found in ANY reply (attacker or customer) marks its zone lost on that event. An attack outcome is "leaked" if its reply leaked any secret. Secrets shorter than 6 letters or digits (the "$2.10" supplier price) only match as a whole token, so "2100" is not a leak.
- engine/rounds.py deleted and engine/judge.py rewritten in Phase 10 (superseded by engine/endless.py and the new judge). is_served is gone, use is_helpful.

- Storage: build_row stores rules_used only for tutorial/level, rules_chars only for endless, guide_skipped only for tutorial, ai_model and ai_temperature only for endless. ENGINE_VERSION is "1.0.0". record_play is offline tested only (no Supabase keys yet).

## Notes for James
- Contract check of your branch claude/practical-mayer-3uwyov (not merged into main yet): ui/data.py calls load_scenario, pick_package and run_level with the section 4 names and shapes. No mismatch found. With this branch your tests/test_app_smoke.py passes against the real engine (checked in a scratch worktree, your files untouched).
- Small difference only in your stand-in (_standin_run_level): it counts every zone of a ring in the totals, the real engine counts only zones attacked or asked about. The stand-in is no longer used once engine/level.py exists.
- main's app.py still imports engine.easy and engine.rounds, which this branch deletes, so app.py on main will not start until your Phase 6 app.py is merged. Expected (master prompt Phase 0 notice).
- Both branches create docs/PROGRESS.md, so the second one merged will get a merge conflict there. Keep both sets of ticks and notes.
- Phase 13 part A: tests pass, no .env, data/ or key like strings (AIza, sb_, eyJ) tracked, requirements.txt installs on Python 3.14.

## Frontend notes (B, James)
Phases 6, 7, 8, 11, 12B and 13B are done. Optional phases 15 and 17 (Endless run interface, level path) were not started. Everything was checked in a real browser with USE_FAKE_AI=true; nothing has been run against real Gemini or Supabase (no keys).

### Decisions
- Map rendering: `st.html` strips SVG in Streamlit 1.67 (the map came out empty), so ui/common.py shows it with `st.markdown(..., unsafe_allow_html=True)` inside a `<div>` so markdown never touches the labels. Every label is escaped in ui/map.py. The map marks a lost inner, sensitive or core zone "leaked" and a lost outer zone "refused" (words, not only colour).
- ui/data.py is the only file in ui/ that imports engine/ and always uses the real engine (the Phase 6 stand-in scenario was removed).
- Playback: a `st.fragment(run_every=0.5)` advances the chat on its own (delay grows with reply length, Slow/Normal/Fast multiply it). The scrubber must not use `on_change` or a forced session value: a timer tick sent the browser's stale slider value back and reset the chat to message 1. It now has a new key per step and any value other than the current message is treated as the player's drag.
- Tutorial guide: sections are `st.container(key="sec_<target>")`, the highlight is CSS on `.st-key-sec_<target>` and the other sections of the screen are dimmed. Step 7 pauses the chat until it is closed. Pressing Start early jumps the guide to step 7.
- Every screen change scrolls to the top with a small script through `st.html(..., unsafe_allow_javascript=True)`. Streamlit only re-runs a script whose text changed, so the script text carries a counter.
- Consent: the checkbox is per run (key includes run_id), unticked by default, and `record_play` is called at most once per run. Loaded saves have no checkbox and are never graded or stored. The player is told when storage is not set up.
- Endless: 30 second cooldown (`ENDLESS_COOLDOWN_SECONDS` in ui/endless.py) counted down by a fragment. Explanations for Endless are built in ui/playback.py (`explain_endless`) from the leaked and refused events, because the engine has no explain function for sections.
- The level screen shows `level["story"]` when present, otherwise the scenario description. Rule cards show the label (toggle) and the rule text only, never side effects. Order is JSON order until Phase 16.
- A Level mode run counts as a pass at one star or more and unlocks the next level; the progress lives in the browser session only.

### Notes
- tests/test_app_smoke.py (B) covers the map, the engine contract against docs/sample_results.json, playback, results, save and load, the guide walkthrough, Endless, the cooldown and the consent rules. It is picked up by tests/run_all.py.
- Known limits: the level select and progress reset when the page is reloaded; Endless was only run with fake AI replies, so helpfulness is low there until a real key is used.
