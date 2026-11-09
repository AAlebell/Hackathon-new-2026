"""The top bar: brand and main navigation, shown on every screen."""

import streamlit as st

from ui import common

NAV = (
    ("Home", "home", ("home",)),
    ("Levels", "levels", ("levels", "level")),
    ("Endless", "endless_select", ("endless_select", "endless")),
)


def current_group() -> str:
    """Return the screens group the player is in; the playback and results belong to their run's mode."""
    state = st.session_state
    screen = state["screen"]
    if screen in ("playback", "results") and state.get("run"):
        return "endless_select" if state["run"]["mode"] == "endless" else "levels"
    return next((target for _, target, screens in NAV if screen in screens), "home")


def topbar() -> None:
    """Show the brand and the Home, Levels and Endless buttons; the current one is highlighted."""
    here = current_group()
    with st.container(key="topbar"):
        brand, *buttons = st.columns([5, 1, 1, 1], gap="small", vertical_alignment="center")
        with brand, st.container(key="brand"):
            st.markdown("\U0001f6e1️ **Chatbot Defense Arena**")
        for column, (label, target, _) in zip(buttons, NAV):
            column.button(label, key=f"nav_{target}", type="primary" if target == here else "tertiary",
                          on_click=common.goto, args=(target,), use_container_width=True)
