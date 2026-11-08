# Progress

Contract: docs/MASTER_PROMPT.md section 4.

## Phases
- [x] Phase 0 (A) Skeleton
- [x] Phase 1 (A) engine/ai.py
- [ ] Phase 2 (A) Loader and tutorial level
- [ ] Phase 3 (A) Level engine
- [ ] Phase 4 (A) Grading
- [ ] Phase 5 (A) Save and load
- [ ] Phase 6 (B) Interface part 1
- [ ] Phase 7 (B) Playback and results
- [ ] Phase 8 (B) Tutorial guide
- [ ] Phase 9 (A) More levels and balance test
- [ ] Phase 10 (A) Endless engine
- [ ] Phase 11 (B) Endless interface
- [ ] Phase 12 Storage (part A / part B)
- [ ] Phase 13 Final checks (part A / part B)

## Decisions
- Person A works on one branch, dong/auto-run, with one pull request for phases 0 to 13A (user request).
- CLAUDE.md contract and scenario shape sections now point to docs/MASTER_PROMPT.md section 4.
- test_engine.py now just runs tests/run_all.py.

- call_ai reads USE_FAKE_AI at call time (not import time), so tests can switch it per process.

## Notes for James
