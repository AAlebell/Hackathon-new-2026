"""Streamlit screens. They use st.session_state and reach the engine only through ui.data."""

import uuid

import streamlit as st

from ui import data
from ui.map import build_map_svg

MAP_LEGEND = ("Outer ring: information Beanie should share with customers. Inner ring: secrets. "
              "Core: the most valuable data. The closer to the centre, the more points.")
STATUS_TEXT = {"open": "▶ Open", "locked": "\U0001f512 Locked"}
STAR = "★"


def goto(screen: str) -> None:
    """Switch to another screen (used as a button callback)."""
    st.session_state["screen"] = screen


def open_level(level_id: str) -> None:
    """Remember the chosen level and show its screen."""
    st.session_state["level_id"] = level_id
    goto("level")


def find_level(scenario: dict, level_id: str) -> dict:
    """Return the level with the given id."""
    for level in scenario["levels"]:
        if level["id"] == level_id:
            return level
    raise ValueError(f"Unknown level: {level_id}")


def level_status(levels: list[dict], index: int, progress: dict) -> str:
    """Return "cleared", "open" or "locked" for the level at the given index."""
    if progress.get(levels[index]["id"], 0) >= 1:
        return "cleared"
    if index == 0 or progress.get(levels[index - 1]["id"], 0) >= 1:
        return "open"
    return "locked"


def rule_key(level_id: str, rule_id: str) -> str:
    """Return the session state key of a rule toggle."""
    return f"rule_{level_id}_{rule_id}"


def selected_rules(level: dict) -> list[str]:
    """Return the ids of the rules the player switched on, in list order."""
    return [rule["id"] for rule in level["rules"]
            if st.session_state.get(rule_key(level["id"], rule["id"]))]


def start_round() -> None:
    """Run the chosen level with the selected rules and move to the playback screen."""
    scenario = data.load_scenario()
    level = find_level(scenario, st.session_state["level_id"])
    chosen = selected_rules(level)
    package_index = data.pick_package(level)
    st.session_state["run"] = {
        "run_id": str(uuid.uuid4()),
        "level_id": level["id"],
        "chosen_rules": chosen,
        "package_index": package_index,
        "result": data.run_level(level, chosen, package_index),
    }
    goto("playback")


def show_svg(svg: str) -> None:
    """Show SVG built by ui.map. st.html strips SVG, so use st.markdown; the div keeps it a raw HTML block."""
    st.markdown(f"<div>{svg}</div>", unsafe_allow_html=True)


def home_screen() -> None:
    """Show the title, the short story and the main buttons."""
    scenario = data.load_scenario()
    st.title("\U0001f6e1️ Chatbot Defense Arena")
    st.write(scenario["description"])
    st.write("You write the rules that protect the chatbot. You score for every secret kept "
             "and every real customer served, so refusing everything never wins.")
    st.button("Play levels", type="primary", key="home_play", on_click=goto, args=("levels",))
    st.button("Endless mode (coming soon)", key="home_endless", disabled=True)


def level_select_screen() -> None:
    """Show every level with its status; the next level opens after a pass."""
    scenario = data.load_scenario()
    levels, progress = scenario["levels"], st.session_state["progress"]
    st.button("← Home", key="levels_back", on_click=goto, args=("home",))
    st.header("Choose a level")
    for index, level in enumerate(levels):
        status = level_status(levels, index, progress)
        with st.container(border=True):
            st.subheader(level["title"])
            st.write(level["theme"])
            stars = progress.get(level["id"], 0)
            st.write(f"{STAR * stars} Cleared" if status == "cleared" else STATUS_TEXT[status])
            st.button("Play" if status != "cleared" else "Play again", key=f"play_{level['id']}",
                      disabled=status == "locked", on_click=open_level, args=(level["id"],))


def rules_panel(level: dict) -> None:
    """Show the rule cards with a toggle each, the count and the cost note."""
    st.subheader("Pick your rules")
    for rule in level["rules"]:
        with st.container(border=True):
            st.toggle(rule["label"], key=rule_key(level["id"], rule["id"]))
            st.write(rule["text"])
    st.write(f"Rules selected: {len(selected_rules(level))}")
    st.caption("Extra rules cost points, so pick only the rules you need.")
    st.button("Start", type="primary", key="start_run", on_click=start_round)


def level_screen() -> None:
    """Show the story, the theme, the map and the rule cards of the current level."""
    scenario = data.load_scenario()
    level = find_level(scenario, st.session_state["level_id"])
    st.button("← Levels", key="level_back", on_click=goto, args=("levels",))
    with st.container(border=True):
        st.header(level["title"])
        st.write(level.get("story") or scenario["description"])
    st.info(f"**Level theme.** {level['theme']}")
    map_col, rules_col = st.columns(2)
    with map_col:
        show_svg(build_map_svg(level["map_zones"]))
        st.caption(MAP_LEGEND)
    with rules_col:
        rules_panel(level)


def playback_screen() -> None:
    """Placeholder until Phase 7 adds chat playback and results."""
    run = st.session_state["run"]
    st.button("← Back to the level", key="playback_back", on_click=goto, args=("level",))
    st.header("Round finished")
    st.write("Chat playback and results arrive in Phase 7. The round already ran:")
    for index, event in enumerate(run["result"]["events"], start=1):
        st.write(f"Message {index}: {event['sender']}, {event['outcome']}")
