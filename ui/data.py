"""Adapter between the interface and the engine, the only file in ui/ that imports engine/."""

import os

from engine.ai import GEMINI_MODEL
from engine.endless import MAX_RULES_CHARS, REPLY_TEMPERATURE, run_section
from engine.grading import FREE_RULES_CHARS, LENGTH_PENALTY, LENGTH_STEP_CHARS, grade_level, penalty
from engine.level import REFUSAL_TIP, explain_result, pick_package, run_level
from engine.save import export_game, import_game
from engine.scenarios import get_guide_steps, load_scenario
from engine.storage import new_session_id, record_play

__all__ = [
    "FREE_RULES_CHARS", "LENGTH_PENALTY", "LENGTH_STEP_CHARS", "MAX_RULES_CHARS", "REFUSAL_TIP",
    "ai_settings", "explain_result", "export_game", "get_guide_steps", "grade_level", "import_game",
    "load_scenario", "new_session_id", "penalty", "pick_package", "record_play", "run_level", "run_section",
]


def ai_settings() -> tuple[str, float]:
    """Return the model name and temperature stored with an Endless run ("fake-ai" in fake mode)."""
    fake = os.getenv("USE_FAKE_AI", "true").strip().lower() == "true"
    return ("fake-ai" if fake else GEMINI_MODEL), REPLY_TEMPERATURE
