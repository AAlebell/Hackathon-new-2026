"""Chatbot Defense Arena, Streamlit entry point. Routes by st.session_state["screen"]."""

import streamlit as st

from ui import data, playback, screens

st.set_page_config(page_title="Chatbot Defense Arena", page_icon="\U0001f6e1️", layout="wide")

SCREENS = {
    "home": screens.home_screen,
    "levels": screens.level_select_screen,
    "level": screens.level_screen,
    "playback": playback.playback_screen,
    "results": playback.results_screen,
}


def init_state() -> None:
    """Set the session defaults once."""
    defaults = {"screen": "home", "level_id": None, "progress": {}, "run": None, "attempts": {},
                "pb_step": 0, "pb_playing": False, "pb_last": 0.0,
                "guide_index": 0, "guide_done": False, "guide_skipped": False}
    for key, value in defaults.items():
        st.session_state.setdefault(key, value)
    if "session_id" not in st.session_state:
        st.session_state["session_id"] = data.new_session_id()


init_state()
SCREENS.get(st.session_state["screen"], screens.home_screen)()
