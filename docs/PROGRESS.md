# Progress

Tick a phase only when its tests pass and it is pushed. Contract: docs/MASTER_PROMPT.md section 4.
Roles: A = engine, scenarios, tests. B = interface, README, docs.

## Phases
- [ ] 0 (A) Skeleton. Started early by B: docs/ files and ui/__init__.py exist. Still open: rewrite CLAUDE.md, add `supabase` to requirements.txt, check .gitignore and .env.example, tests/run_all.py
- [ ] 1 (A) engine/ai.py
- [ ] 2 (A) Loader and tutorial level
- [ ] 3 (A) Level engine
- [ ] 4 (A) Grading
- [ ] 5 (A) Save and load
- [x] 6 (B) Interface part 1: home, level select, level screen, map
- [ ] 7 (B) Playback and results
- [ ] 8 (B) Tutorial guide
- [ ] 9 (A) More levels and balance test
- [ ] 10 (A) Endless engine
- [ ] 11 (B) Endless interface
- [ ] 12A (A) engine/storage.py
- [ ] 12B (B) Consent checkbox and result storage
- [ ] 13A (A) Final checks
- [ ] 13B (B) README
- [ ] 14 (A) Endless run, optional
- [ ] 15 (B) Endless run interface, optional
- [ ] 16 (A) Shop per try, optional
- [ ] 17 (B) Level path and worlds, optional
- [ ] 18 (A) More worlds, optional

## Decisions
- Map rendering: `st.html` strips SVG in Streamlit 1.67 (the map came out empty), so ui/screens.py shows it with `st.markdown(..., unsafe_allow_html=True)` inside a `<div>` so markdown never touches the labels. Every label is escaped in ui/map.py.
- docs/sample_results.json did not exist, so B created it. Shape: `{"scenario": <section 4.1 scenario with tutorial_1>, "runs": {name: {chosen_rules, package_index, result, explanation, grade}}}`. Five runs: perfect (score 100), perfect plus an extra rule (95, 3 stars, not perfect), be_polite only (core hacked, lose), refuse_all (50, fail), only_menu_topics (67, 1 star).
- docs/supabase.sql was created from the SQL in PLAN.md section 7.1.
- Until engine/level.py exists, ui/data.py uses a stand-in `run_level` and the sample scenario. It switches to the real engine by itself once engine/level.py exists (`importlib.util.find_spec`). Nothing else in ui/ imports engine/.
- `event["step"]` is the zero-based index in `events`. The interface relies on list order, not on this value.
- Security total is the points of every inner, sensitive and core zone, helpfulness total is the points of every outer zone. Score is rounded half up to an int.
- The level screen shows `level["story"]` when present, otherwise the scenario description (the contract has no story field).
- Rule cards show the label (toggle) and the rule text only, never side effects. Order is JSON order until Phase 16.
- The playback screen is a stub until Phase 7.
- Not copied into docs/: the Vietnamese division-of-work file and the .docx (internal team notes, and the docx duplicates PLAN.md).

## Notes for the other role
- For A, Phase 0 is still open. CLAUDE.md still describes the old Easy and Medium contract (run_round, resolve_choice). The old engine (engine/rounds.py, engine/easy.py, the old scenarios/cafe.json, test_engine.py) is still in the repo. Phases 2 and 3 replace it. app.py no longer uses any of it.
- When A writes tutorial_1, keep the ids from Phase 2 (rules `no_internal_codes`, `only_menu_topics`, `refuse_all`, `be_polite`, zones `hours`, `menu`, `wifi`, `staff_code`, `member_data`). Then `python tests/test_app_smoke.py` checks your `run_level` against docs/sample_results.json (outcomes, maps and scores, not reply wording) and walks the screens.
- Pull requests: work goes to a branch and is merged by PR, not pushed to main (see CLAUDE.md "Working together").
