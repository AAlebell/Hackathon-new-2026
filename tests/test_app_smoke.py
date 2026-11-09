"""Smoke tests for the interface: map SVG, adapter and the screen flow. Run: python tests/test_app_smoke.py"""

import json
import os
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
os.environ["USE_FAKE_AI"] = "true"

from streamlit.testing.v1 import AppTest  # noqa: E402

from ui import common, data, playback  # noqa: E402
from ui.map import build_map_svg  # noqa: E402
from ui.screens import level_status  # noqa: E402

APP = str(ROOT / "app.py")
SCENARIO = data.load_scenario("cafe")
LEVEL = SCENARIO["levels"][0]
SAMPLE = json.loads((ROOT / "docs" / "sample_results.json").read_text(encoding="utf-8"))
GOOD_RULE = f"rule_{LEVEL['id']}_no_internal_codes"


def new_app() -> AppTest:
    """Return a fresh app that has run once."""
    return AppTest.from_file(APP, default_timeout=30).run()


def at_results(rules: tuple[str, ...] = ("no_internal_codes",)) -> AppTest:
    """Play tutorial_1 with the given rules through the screens and return the app on the results screen."""
    at = new_app()
    at.button(key="home_play").click().run()
    at.button(key=f"play_{LEVEL['id']}").click().run()
    for rule in rules:
        at.toggle(key=f"rule_{LEVEL['id']}_{rule}").set_value(True).run()
    at.button(key="start_run").click().run()
    at.button(key="pb_all").click().run()
    at.button(key="pb_results").click().run()
    return at


# ---- map ---------------------------------------------------------------------------------------

def test_map_svg() -> None:
    """The map is well formed, shows every zone and marks lost zones with words, not only colour."""
    zones = LEVEL["map_zones"]
    secret = next(z["id"] for z in zones if z["ring"] != "outer")
    outer = next(z["id"] for z in zones if z["ring"] == "outer")
    svg = build_map_svg(zones, state={secret: "lost", outer: "lost"}, attacked=outer)
    ET.fromstring(svg)  # raises if the SVG is not well formed
    for zone in zones:
        assert zone["label"].split()[0] in svg, zone["id"]
    assert svg.count('data-state="lost"') == 2
    assert "✕ leaked" in svg and "⊘ refused" in svg
    assert svg.count("#d62828") == 1  # only the attacked zone has the red outline


def test_map_escapes_labels() -> None:
    """A label with HTML never reaches the page as HTML."""
    zones = [{"id": "x", "label": "<script>alert(1)</script>", "ring": "outer", "points": 10}]
    svg = build_map_svg(zones)
    assert "<script>" not in svg and "&lt;script&gt;" in svg
    ET.fromstring(svg)


def test_map_rejects_unknown_ring() -> None:
    """An unknown ring name is an error, not a missing zone."""
    try:
        build_map_svg([{"id": "x", "label": "X", "ring": "middle", "points": 1}])
    except ValueError:
        return
    raise AssertionError("expected ValueError")


# ---- engine contract ---------------------------------------------------------------------------

def structure(result: dict) -> dict:
    """Keep outcomes, maps and scores of a result and drop the reply wording."""
    keys = ("step", "sender", "zone", "outcome", "map")
    summary = {k: result[k] for k in ("security", "helpfulness", "core_hacked", "rules_used", "package_index")}
    summary["events"] = [{k: event[k] for k in keys} for event in result["events"]]
    return summary


def test_run_level_matches_sample_runs() -> None:
    """run_level reproduces the outcomes, maps and scores of every reference run in docs/sample_results.json."""
    for name, run in SAMPLE["samples"].items():
        got = data.run_level(LEVEL, run["chosen_rules"], run["result"]["package_index"])
        assert structure(got) == structure(run["result"]), name


def test_sample_zones_match_level() -> None:
    """The level keeps the zone ids, rings and points listed in docs/sample_results.json."""
    keys = ("id", "ring", "points")
    shorten = lambda zones: [{k: zone[k] for k in keys} for zone in zones]  # noqa: E731
    assert shorten(LEVEL["map_zones"]) == shorten(SAMPLE["map_zones"])


def test_tutorial_has_guide_steps() -> None:
    """The first level carries the 10 tutorial guide steps."""
    assert len(data.get_guide_steps(LEVEL)) == 10


def test_unknown_rule_raises() -> None:
    """An unknown rule id raises ValueError."""
    try:
        data.run_level(LEVEL, ["no_such_rule"], 0)
    except ValueError:
        return
    raise AssertionError("expected ValueError")


def test_level_status() -> None:
    """The first level is open, the next opens after a pass, a passed level is cleared."""
    levels = [{"id": "a"}, {"id": "b"}, {"id": "c"}]
    assert [level_status(levels, i, {}) for i in range(3)] == ["open", "locked", "locked"]
    assert [level_status(levels, i, {"a": 2}) for i in range(3)] == ["cleared", "open", "locked"]


# ---- playback, results, save and load ----------------------------------------------------------

def test_message_delay() -> None:
    """Long replies stay longer and Fast is quicker than Slow."""
    short, long_ = {"reply": "Hi"}, {"reply": "x" * 300}
    assert playback.message_delay(long_, "Normal") > playback.message_delay(short, "Normal")
    assert playback.message_delay(short, "Fast") < playback.message_delay(short, "Slow")


def test_screen_flow() -> None:
    """Home, level select, level screen, Start, playback controls and the results screen all work."""
    at = new_app()
    assert not at.exception and at.title[0].value.endswith("Chatbot Defense Arena")
    at.button(key="home_play").click().run()
    assert at.session_state["screen"] == "levels" and not at.exception
    at.button(key=f"play_{LEVEL['id']}").click().run()
    assert at.session_state["screen"] == "level" and len(at.toggle) == len(LEVEL["rules"])
    at.button(key="guide_skip").click().run()  # the guide has its own tests below

    at.toggle(key=GOOD_RULE).set_value(True).run()
    at.button(key="start_run").click().run()
    assert at.session_state["screen"] == "playback" and not at.exception
    assert at.session_state["pb_step"] == 0 and at.session_state["pb_playing"]
    events = at.session_state["run"]["result"]["events"]
    assert [e["outcome"] for e in events] == ["blocked", "served", "blocked", "served", "served"]

    at.button(key="pb_next").click().run()
    assert at.session_state["pb_step"] == 1 and not at.session_state["pb_playing"]
    at.button(key="pb_toggle").click().run()
    assert at.session_state["pb_playing"]
    at.button(key="pb_all").click().run()
    assert at.session_state["pb_step"] == len(events) - 1
    at.button(key="pb_results").click().run()
    assert at.session_state["screen"] == "results" and not at.exception

    assert any("Perfect" in banner.value for banner in at.success)
    assert [m.label for m in at.metric] == ["Security", "Helpfulness", "Penalty", "Score"]
    assert at.session_state["progress"][LEVEL["id"]] == 3

    at.button(key="rs_replay").click().run()
    assert at.session_state["screen"] == "playback" and at.session_state["pb_step"] == 0
    at.button(key="pb_back").click().run()
    assert at.session_state["screen"] == "level"


def test_scrubber_jumps_to_a_message_and_pauses() -> None:
    """Dragging the slider shows that message and pauses; the slider never moves the step by itself."""
    at = new_app()
    at.button(key="home_play").click().run()
    at.button(key=f"play_{LEVEL['id']}").click().run()
    at.button(key="guide_skip").click().run()
    at.button(key="start_run").click().run()
    assert at.session_state["pb_step"] == 0 and at.session_state["pb_playing"]
    at.slider(key="pb_slider_0").set_value(4).run()
    assert at.session_state["pb_step"] == 3 and not at.session_state["pb_playing"] and not at.exception
    assert at.slider(key="pb_slider_3").value == 4
    at.run()  # a plain rerun (like a timer tick) must not change the step
    assert at.session_state["pb_step"] == 3


def test_results_explain_a_leak_and_a_refusal() -> None:
    """A run that leaks shows the attack type and coach tip; a run that refuses names the rule to blame."""
    at = at_results(rules=("be_polite",))
    assert at.error and "core was hacked" in at.error[0].value
    assert any("Coach tip" in info.value for info in at.info)
    at = at_results(rules=("refuse_all",))
    assert any("Rule that turned them away" in md.value for md in at.markdown)
    assert at.session_state["progress"] == {}  # a fail does not unlock the next level
    assert at.button(key="rs_next").disabled


def test_save_and_load_roundtrip() -> None:
    """A saved round loads back as a replay-only run; bad files are rejected with a clear message."""
    at = at_results()
    run = at.session_state["run"]
    text = data.export_game(playback.save_record(run))
    loaded = playback.run_from_save(data.import_game(text))
    assert loaded["loaded"] and loaded["recorded"] and loaded["level_id"] == LEVEL["id"]
    assert loaded["result"]["events"] == run["result"]["events"]
    bad = {"format": "chatbot-defense-arena/1", "level_id": "no_such_level", "result": {"events": run["result"]["events"]}}
    for broken in (bad, {"format": "chatbot-defense-arena/1", "level_id": LEVEL["id"], "events": [{"sender": "x"}]},
                   {"format": "chatbot-defense-arena/1", "level_id": LEVEL["id"], "events": []}):
        try:
            playback.run_from_save(broken)
        except ValueError:
            continue
        raise AssertionError("expected ValueError")


def test_explain_endless() -> None:
    """Endless explanations name the attack type and carry the section's coach tip."""
    section = SCENARIO["sections"][0]
    result = data.run_section(section, "", 0)
    items = playback.explain_endless(section, result)
    assert items and all(item["coach_tip"] for item in items)
    assert {item["kind"] for item in items} <= {"leak", "refusal"}


def guide_title(at: AppTest) -> str:
    """Return the guide box heading currently on screen, or an empty string."""
    return next((m.value for m in at.markdown if m.value.startswith("**Tutorial, step")), "")


def test_guide_walkthrough() -> None:
    """The 10 steps appear in order: 1 to 6 before the round, 7 pauses the chat, 8 to 10 on the results."""
    at = new_app()
    at.button(key="home_play").click().run()
    at.button(key=f"play_{LEVEL['id']}").click().run()
    steps = data.get_guide_steps(LEVEL)
    for number in range(1, 7):
        assert f"step {number} of 10: {steps[number - 1]['title']}" in guide_title(at), number
        at.button(key="guide_next").click().run()
    assert guide_title(at) == ""  # steps 7 to 10 do not belong to the level screen

    at.toggle(key=GOOD_RULE).set_value(True).run()
    at.button(key="start_run").click().run()
    assert f"step 7 of 10: {steps[6]['title']}" in guide_title(at)
    assert at.session_state["pb_step"] == 0 and not at.session_state["pb_playing"]  # chat paused by the guide
    at.button(key="guide_next").click().run()
    assert at.session_state["pb_playing"] and guide_title(at) == ""
    at.button(key="pb_all").click().run()
    at.button(key="pb_results").click().run()
    for number in (8, 9, 10):
        assert f"step {number} of 10: {steps[number - 1]['title']}" in guide_title(at), number
        button = at.button(key="guide_next")
        assert button.label == ("Got it" if number == 10 else "Next")
        button.click().run()
    assert at.session_state["guide_done"] and not at.session_state["guide_skipped"]
    assert guide_title(at) == "" and not at.exception


def test_guide_skip_help_and_early_start() -> None:
    """Skip closes the guide, Help restarts it, and pressing Start early still shows step 7."""
    at = new_app()
    at.button(key="home_play").click().run()
    at.button(key=f"play_{LEVEL['id']}").click().run()
    at.button(key="guide_skip").click().run()
    assert at.session_state["guide_done"] and at.session_state["guide_skipped"] and guide_title(at) == ""
    at.button(key="level_help").click().run()
    assert at.session_state["guide_index"] == 0 and "step 1 of 10" in guide_title(at)
    at.toggle(key=GOOD_RULE).set_value(True).run()
    at.button(key="start_run").click().run()  # still on step 1
    assert "step 7 of 10" in guide_title(at) and not at.session_state["pb_playing"]


def test_level_without_guide_has_no_guide_box_or_help() -> None:
    """Only levels with guide steps show the guide and the Help button."""
    plain = next(level for level in SCENARIO["levels"] if not data.get_guide_steps(level))
    at = AppTest.from_file(APP, default_timeout=30)
    at.session_state["screen"] = "level"
    at.session_state["level_id"] = plain["id"]
    at.run()
    assert guide_title(at) == "" and not [b for b in at.button if b.key == "level_help"]


def test_guide_css_targets_one_section() -> None:
    """The highlight outlines the target and dims every other section of that screen only."""
    from ui import guide

    css = guide.highlight_css("level", "map")
    assert ".st-key-sec_map {outline" in css and ".st-key-sec_story" in css and ".st-key-sec_chat" not in css
    assert css.count("opacity") == 1


def test_every_level_screen_opens() -> None:
    """Every level opens its screen with one toggle per rule and runs with every rule switched on."""
    for level in SCENARIO["levels"]:
        at = AppTest.from_file(APP, default_timeout=30)
        at.session_state["screen"] = "level"
        at.session_state["level_id"] = level["id"]
        at.run()
        assert not at.exception, level["id"]
        assert len(at.toggle) == len(level["rules"]), level["id"]
        for toggle in at.toggle:
            toggle.set_value(True)
        at.run()
        at.button(key="start_run").click().run()
        assert not at.exception and at.session_state["screen"] == "playback", level["id"]
        at.button(key="pb_all").click().run()
        at.button(key="pb_results").click().run()
        assert not at.exception and at.session_state["screen"] == "results", level["id"]


if __name__ == "__main__":
    for name, test in sorted(globals().items()):
        if name.startswith("test_") and callable(test):
            test()
            print(f"ok  {name}")
