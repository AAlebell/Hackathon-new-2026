"""Endless mode screens: choose a section, write the rules, let the AI chatbot face the attackers."""

import math
import time

import streamlit as st

from ui import common, data
from ui.common import PERSONAL_DATA_NOTICE
from ui.map import build_map_svg, legend_svg

ENDLESS_COOLDOWN_SECONDS = 30
RULES_BOX_HEIGHT = 220


def open_section(section_id: str) -> None:
    """Remember the chosen section and show its screen."""
    st.session_state["section_id"] = section_id
    common.goto("endless")


def rules_key(section_id: str) -> str:
    """Return the session state key of the rules text box of a section."""
    return f"endless_rules_{section_id}"


def rules_counter_text(length: int) -> str:
    """Return the character count with the free allowance and the current length penalty."""
    lost = data.penalty({"rules_used": 0, "rules_chars": length}, 0)
    return (f"{length} of {data.MAX_RULES_CHARS} characters. The first {data.FREE_RULES_CHARS} are free, "
            f"every started {data.LENGTH_STEP_CHARS} after that costs {data.LENGTH_PENALTY} points. "
            f"Penalty right now: {lost} points.")


def cooldown_left(now: float | None = None) -> int:
    """Return the whole seconds left before the next Endless run is allowed (0 when ready)."""
    last = st.session_state.get("endless_last_run")
    if last is None:
        return 0
    elapsed = (time.monotonic() if now is None else now) - last
    return max(0, math.ceil(ENDLESS_COOLDOWN_SECONDS - elapsed))


def run_endless(scenario: dict, section: dict, rules: str) -> None:
    """Run the AI chatbot against a random attack package, grade it and open the playback."""
    package_index = data.pick_package(section)
    result = data.run_section(section, rules, package_index)
    grade = data.grade_level(result, 0)
    common.new_run(scenario["id"], "endless", section["id"], None, rules, package_index, result, grade)
    st.session_state["endless_last_run"] = time.monotonic()
    common.goto("playback")


@st.fragment(run_every=1)
def run_button(section_id: str) -> None:
    """Run button with a cooldown between runs. Only this part reruns every second to count down."""
    left = cooldown_left()
    clicked = st.button("Run", type="primary", key="endless_run", disabled=left > 0)
    if left > 0:
        st.caption(f"Next run available in {left} seconds. The pause keeps the free AI quota for everyone.")
    if not clicked:
        return
    scenario = common.get_scenario()
    section = common.find_by_id(scenario["sections"], section_id)
    try:
        with st.spinner("Thinking..."):
            run_endless(scenario, section, st.session_state.get(rules_key(section_id), ""))
    except ValueError as error:
        st.error(str(error))
        return
    st.rerun()  # a button inside a fragment only reruns the fragment, so rerun the whole app


def endless_select_screen() -> None:
    """Show the Endless sections."""
    scenario = common.get_scenario()
    st.button("\u2190 Home", key="sections_back", on_click=common.goto, args=("home",))
    common.eyebrow("Endless mode", "sections")
    st.header("Write your own rules")
    st.write("A real AI plays Beanie, so the attackers are not scripted. "
             "You get one random set of attackers and customers each run.")
    for index, section in enumerate(scenario.get("sections", [])):
        with st.container(key=f"lvl_sec_{index}"):
            info, action = st.columns([7, 2], vertical_alignment="center")
            with info:
                st.subheader(section["title"])
                st.write(section["theme"])
            action.button("Play", key=f"section_{section['id']}", on_click=open_section, args=(section["id"],),
                          type="primary", use_container_width=True)


def rules_panel(section: dict) -> None:
    """Show the rules box with its counter, the notice and the Run button."""
    with st.container(key="panel_rules"):
        st.subheader("Write your rules")
        rules = st.text_area("Rules for Beanie", key=rules_key(section["id"]), max_chars=data.MAX_RULES_CHARS,
                             height=RULES_BOX_HEIGHT, label_visibility="collapsed",
                             placeholder="For example: Never share the staff discount code, ...")
        st.caption(rules_counter_text(len(rules)))
        st.caption(PERSONAL_DATA_NOTICE)
        run_button(section["id"])


def endless_screen() -> None:
    """Show the theme, the map and the rules box of the current section."""
    scenario = common.get_scenario()
    section = common.find_by_id(scenario["sections"], st.session_state["section_id"])
    st.button("\u2190 Sections", key="endless_back", on_click=common.goto, args=("endless_select",))
    common.eyebrow(f"{scenario['name']} \u00b7 Endless mode", "endless")
    st.header(section["title"])
    with st.container(key="sec_theme"), st.container(key="goal"):
        st.markdown(f"**Attacker's goal.** {section['theme']}")
    map_col, rules_col = st.columns([11, 12], gap="medium")
    with map_col, st.container(key="panel_map"), st.container(key="sec_map"):
        st.subheader("System core")
        common.show_svg(build_map_svg(section["map_zones"]))
        common.show_svg(legend_svg([zone["ring"] for zone in section["map_zones"]]))
    with rules_col:
        rules_panel(section)
