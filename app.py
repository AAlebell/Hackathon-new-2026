"""Chatbot Defense Arena, Streamlit entry point. Routes by st.session_state["screen"]."""

import streamlit as st

from ui import screens

st.set_page_config(page_title="Chatbot Defense Arena", page_icon="\U0001f6e1️", layout="wide")

SCREENS = {
    "home": screens.home_screen,
    "levels": screens.level_select_screen,
    "level": screens.level_screen,
    "playback": screens.playback_screen,
}


def init_state() -> None:
    """Set the session defaults once."""
    defaults = {"screen": "home", "level_id": None, "progress": {}, "run": None}
    for key, value in defaults.items():
        st.session_state.setdefault(key, value)


init_state()
SCREENS.get(st.session_state["screen"], screens.home_screen)()
