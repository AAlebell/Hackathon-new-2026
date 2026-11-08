"""Adapter between the interface and the engine, the only file in ui/ that touches engine/.

Once engine/level.py exists this file calls the real engine. Until then it falls back to
docs/sample_results.json and a small stand-in for run_level, so the interface can be built
and played on its own. The switch is automatic, nothing in app.py or ui/screens.py changes.
"""

import copy
import importlib.util
import json
import random
from functools import lru_cache
from pathlib import Path

SAMPLE_PATH = Path(__file__).resolve().parent.parent / "docs" / "sample_results.json"
SECRET_RINGS = ("inner", "sensitive", "core")


def using_real_engine() -> bool:
    """Return True once the real level engine (engine/level.py) exists."""
    try:
        return importlib.util.find_spec("engine.level") is not None
    except (ImportError, ValueError):
        return False


@lru_cache(maxsize=1)
def _sample() -> dict:
    """Read docs/sample_results.json once."""
    return json.loads(SAMPLE_PATH.read_text(encoding="utf-8"))


def sample_runs() -> dict:
    """Return the canned runs, used by tests to check the engine against the contract."""
    return copy.deepcopy(_sample()["runs"])


def load_scenario(scenario_id: str = "cafe") -> dict:
    """Return a validated scenario dict (section 4.1 of the contract)."""
    if using_real_engine():
        from engine.scenarios import load_scenario as real_load

        return real_load(scenario_id)
    scenario = copy.deepcopy(_sample()["scenario"])
    if scenario["id"] != scenario_id:
        raise ValueError(f"Unknown scenario: {scenario_id}")
    return scenario


def pick_package(level: dict, rng: random.Random | None = None) -> int:
    """Return the index of the attack package to play."""
    if using_real_engine():
        from engine.level import pick_package as real_pick

        return real_pick(level, rng)
    return (rng or random).randrange(len(level["attack_packages"]))


def run_level(level: dict, chosen_rules: list[str], package_index: int) -> dict:
    """Play a scripted level and return the result (section 4.2 of the contract)."""
    if using_real_engine():
        from engine.level import run_level as real_run

        return real_run(level, chosen_rules, package_index)
    return _standin_run_level(level, chosen_rules, package_index)


def _interleave(attacks: list[dict], customers: list[dict]) -> list[tuple[str, dict]]:
    """Alternate attack, customer, attack, customer, with leftovers at the end."""
    order: list[tuple[str, dict]] = []
    for i in range(max(len(attacks), len(customers))):
        if i < len(attacks):
            order.append(("attacker", attacks[i]))
        if i < len(customers):
            order.append(("customer", customers[i]))
    return order


def _play_step(step: int, sender: str, item: dict, chosen: list[str], state: dict) -> dict:
    """Apply one message to the map state and return its event."""
    if sender == "attacker":
        blocked = any(rule in item["blocked_by"] for rule in chosen)
        zone, lost = item["target_zone"], not blocked
        outcome = "blocked" if blocked else "leaked"
        reply = item["reply_if_blocked" if blocked else "reply_if_leaked"]
    else:
        refused = any(rule in item["broken_by"] for rule in chosen)
        zone, lost = item["zone"], refused
        outcome = "refused" if refused else "served"
        reply = item["reply_refused" if refused else "reply_ok"]
    if lost:
        state[zone] = "lost"
    return {"step": step, "sender": sender, "text": item["text"], "reply": reply,
            "zone": zone, "outcome": outcome, "map": dict(state)}


def _points(zones: list[dict], state: dict, rings: tuple[str, ...]) -> dict:
    """Return earned and total points for the zones on the given rings."""
    chosen = [z for z in zones if z["ring"] in rings]
    return {"earned": sum(z["points"] for z in chosen if state[z["id"]] == "safe"),
            "total": sum(z["points"] for z in chosen)}


def _standin_run_level(level: dict, chosen_rules: list[str], package_index: int) -> dict:
    """Stand-in for engine.level.run_level, used only until the real engine exists."""
    known = {rule["id"] for rule in level["rules"]}
    for rule_id in chosen_rules:
        if rule_id not in known:
            raise ValueError(f"Unknown rule id: {rule_id}")
    zones = level["map_zones"]
    state = {zone["id"]: "safe" for zone in zones}
    order = _interleave(level["attack_packages"][package_index], level["customer_questions"])
    events = [_play_step(i, sender, item, chosen_rules, state)
              for i, (sender, item) in enumerate(order)]
    core_ids = [zone["id"] for zone in zones if zone["ring"] == "core"]
    return {"events": events,
            "security": _points(zones, state, SECRET_RINGS),
            "helpfulness": _points(zones, state, ("outer",)),
            "core_hacked": any(state[zone_id] == "lost" for zone_id in core_ids),
            "rules_used": len(chosen_rules),
            "package_index": package_index}
