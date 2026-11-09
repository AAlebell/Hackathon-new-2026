"""Home, level select and level screens. They use st.session_state and reach the engine only through ui.data."""

import streamlit as st

from ui import common, data, guide
from ui.common import PERSONAL_DATA_NOTICE, STAR
from ui.map import build_map_svg
from ui.playback import load_game_widget

MAP_LEGEND = ("Outer ring: information Beanie should share with customers. Inner ring: secrets. "
              "Core: the most valuable data. The closer to the centre, the more points.")
STATUS_TEXT = {"open": "▶ Open", "locked": "\U0001f512 Locked"}


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
    scenario = common.get_scenario()
    level = common.find_by_id(scenario["levels"], st.session_state["level_id"])
    chosen = selected_rules(level)
    package_index = data.pick_package(level)
    result = data.run_level(level, chosen, package_index)
    grade = data.grade_level(result, level["min_rules"])
    common.new_run(scenario["id"], "level", level["id"], chosen, None, package_index, result, grade)
    common.goto("playback")


def home_screen() -> None:
    """Show the title, the short story and the main buttons."""
    scenario = common.get_scenario()
    st.title("\U0001f6e1️ Chatbot Defense Arena")
    st.write(scenario["description"])
    st.write("You write the rules that protect the chatbot. You score for every secret kept "
             "and every real customer served, so refusing everything never wins.")
    st.button("Play levels", type="primary", key="home_play", on_click=common.goto, args=("levels",))
    st.button("Endless mode", key="home_endless", on_click=common.goto, args=("endless_select",),
              disabled=not scenario.get("sections"))
    load_game_widget("load_home")


def level_select_screen() -> None:
    """Show every level with its status; the next level opens after a pass."""
    scenario = common.get_scenario()
    levels, progress = scenario["levels"], st.session_state["progress"]
    st.button("← Home", key="levels_back", on_click=common.goto, args=("home",))
    st.header("Choose a level")
    for index, level in enumerate(levels):
        status = level_status(levels, index, progress)
        with st.container(border=True):
            st.subheader(level["title"])
            st.write(level["theme"])
            stars = progress.get(level["id"], 0)
            st.write(f"{STAR * stars} Cleared" if status == "cleared" else STATUS_TEXT[status])
            st.button("Play" if status != "cleared" else "Play again", key=f"play_{level['id']}",
                      disabled=status == "locked", on_click=common.open_level, args=(level["id"],))


def rules_panel(level: dict) -> None:
    """Show the rule cards with a toggle each, the count, the cost note and the Start button."""
    with st.container(key="sec_rules"):
        st.subheader("Pick your rules")
        for rule in level["rules"]:
            with st.container(border=True):
                st.toggle(rule["label"], key=rule_key(level["id"], rule["id"]))
                st.write(rule["text"])
        st.write(f"Rules selected: {len(selected_rules(level))}")
        st.caption("Extra rules cost points, so pick only the rules you need. " + PERSONAL_DATA_NOTICE)
    with st.container(key="sec_start_button"):
        st.button("Start", type="primary", key="start_run", on_click=start_round)


def level_screen() -> None:
    """Show the story, the theme, the map and the rule cards of the current level."""
    scenario = common.get_scenario()
    level = common.find_by_id(scenario["levels"], st.session_state["level_id"])
    back_col, help_col, _ = st.columns([1, 1, 6])
    back_col.button("← Levels", key="level_back", on_click=common.goto, args=("levels",))
    if data.get_guide_steps(level):
        help_col.button("Help", key="level_help", on_click=guide.restart)
    guide.show("level", level)
    with st.container(key="sec_story"), st.container(border=True):
        st.header(level["title"])
        st.write(level.get("story") or scenario["description"])
    with st.container(key="sec_theme"):
        st.info(f"**Level theme.** {level['theme']}")
    map_col, rules_col = st.columns(2)
    with map_col, st.container(key="sec_map"):
        common.show_svg(build_map_svg(level["map_zones"]))
        st.caption(MAP_LEGEND)
    with rules_col:
        rules_panel(level)
