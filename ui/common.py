"""Small helpers shared by all screens: navigation, lookups and creating a finished run."""

import time
import uuid
from functools import lru_cache

import streamlit as st

from ui import data

STAR = "★"
PERSONAL_DATA_NOTICE = "Do not enter real personal information."


def show_svg(svg: str) -> None:
    """Show SVG built by ui.map. st.html strips SVG, so use st.markdown; the div keeps it a raw HTML block."""
    st.markdown(f"<div>{svg}</div>", unsafe_allow_html=True)


def goto(screen: str) -> None:
    """Switch to another screen (used as a button callback)."""
    st.session_state["screen"] = screen


def open_level(level_id: str) -> None:
    """Remember the chosen level and show its screen."""
    st.session_state["level_id"] = level_id
    goto("level")


@lru_cache(maxsize=4)
def get_scenario(scenario_id: str = "cafe") -> dict:
    """Load a scenario once. Callers must treat the result as read only."""
    return data.load_scenario(scenario_id)


def find_by_id(items: list[dict], item_id: str) -> dict:
    """Return the level or section with the given id."""
    for item in items:
        if item["id"] == item_id:
            return item
    raise ValueError(f"Unknown id: {item_id}")


def find_source(scenario_id: str, mode: str, source_id: str) -> dict:
    """Return the level (Level mode) or section (Endless mode) a run was played on."""
    scenario = get_scenario(scenario_id)
    return find_by_id(scenario["sections" if mode == "endless" else "levels"], source_id)


def run_source(run: dict) -> dict:
    """Return the level or section of a run."""
    return find_source(run["scenario_id"], run["mode"], run["level_id"])


def storage_mode(mode: str, source_id: str) -> str:
    """Return the storage mode: endless, tutorial (ids starting with tutorial) or level."""
    if mode == "endless":
        return "endless"
    return "tutorial" if source_id.startswith("tutorial") else "level"


def start_playback() -> None:
    """Show the first message of the current run and let the chat play on its own."""
    st.session_state.update(pb_step=0, pb_playing=True, pb_last=time.monotonic())


def new_run(scenario_id: str, mode: str, source_id: str, chosen_rules: list[str] | None,
            player_rules: str | None, package_index: int, result: dict, grade: dict) -> None:
    """Store a finished run, count the attempt, update level progress and start its playback."""
    state = st.session_state
    state["attempts"][source_id] = state["attempts"].get(source_id, 0) + 1
    if mode == "level" and grade["stars"] >= 1:
        state["progress"][source_id] = max(state["progress"].get(source_id, 0), grade["stars"])
    state["run"] = {
        "run_id": str(uuid.uuid4()), "mode": mode, "scenario_id": scenario_id, "level_id": source_id,
        "chosen_rules": chosen_rules, "player_rules": player_rules, "package_index": package_index,
        "result": result, "grade": grade, "attempt": state["attempts"][source_id],
        "loaded": False, "recorded": False, "saved": False,
    }
    start_playback()
