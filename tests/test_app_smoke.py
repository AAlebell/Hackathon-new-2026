"""Smoke tests for the interface: map SVG, adapter and the screen flow. Run: python tests/test_app_smoke.py"""

import os
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
os.environ["USE_FAKE_AI"] = "true"

from streamlit.testing.v1 import AppTest  # noqa: E402

from ui import data  # noqa: E402
from ui.map import build_map_svg  # noqa: E402
from ui.screens import level_status  # noqa: E402

APP = str(Path(__file__).resolve().parent.parent / "app.py")
SCENARIO = data.load_scenario()
LEVEL = SCENARIO["levels"][0]


def test_map_svg() -> None:
    """The map is well formed, shows every zone and marks lost zones with text, not only colour."""
    svg = build_map_svg(LEVEL["map_zones"], state={"staff_code": "lost"}, attacked="hours")
    ET.fromstring(svg)  # raises if the SVG is not well formed
    for zone in LEVEL["map_zones"]:
        assert zone["label"].split()[0] in svg, zone["id"]
    assert svg.count('data-state="lost"') == 1
    assert "✕ lost" in svg
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


def structure(result: dict) -> dict:
    """Keep outcomes, maps and scores of a result and drop the reply wording."""
    keys = ("step", "sender", "zone", "outcome", "map")
    summary = {k: result[k] for k in ("security", "helpfulness", "core_hacked", "rules_used", "package_index")}
    summary["events"] = [{k: event[k] for k in keys} for event in result["events"]]
    return summary


def test_run_level_matches_sample_runs() -> None:
    """run_level (stand-in or real engine) reproduces the outcomes, maps and scores of every canned run."""
    for name, run in data.sample_runs().items():
        got = data.run_level(LEVEL, run["chosen_rules"], run["package_index"])
        assert structure(got) == structure(run["result"]), name


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


def test_screen_flow() -> None:
    """Home, level select, level screen, Start and the playback screen all work."""
    at = AppTest.from_file(APP, default_timeout=30).run()
    assert not at.exception and at.title[0].value.endswith("Chatbot Defense Arena")
    assert at.button(key="home_endless").disabled

    at.button(key="home_play").click().run()
    assert at.session_state["screen"] == "levels" and not at.exception

    at.button(key=f"play_{LEVEL['id']}").click().run()
    assert at.session_state["screen"] == "level" and not at.exception
    assert len(at.toggle) == len(LEVEL["rules"])

    at.toggle(key=f"rule_{LEVEL['id']}_no_internal_codes").set_value(True).run()
    at.button(key="start_run").click().run()
    assert at.session_state["screen"] == "playback" and not at.exception
    run = at.session_state["run"]
    assert run["chosen_rules"] == ["no_internal_codes"] and run["run_id"]
    outcomes = [event["outcome"] for event in run["result"]["events"]]
    assert outcomes == ["blocked", "served", "blocked", "served", "served"], outcomes


if __name__ == "__main__":
    for name, test in sorted(globals().items()):
        if name.startswith("test_") and callable(test):
            test()
            print(f"ok  {name}")
