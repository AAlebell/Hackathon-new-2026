"""Chat playback and the results screen, shared by Level mode and Endless mode."""

import time
import uuid

import streamlit as st

from ui import common, data
from ui.common import STAR
from ui.map import build_map_svg

SPEEDS = {"Slow": 1.6, "Normal": 1.0, "Fast": 0.4}
BASE_DELAY_SECONDS = 2.0
SECONDS_PER_CHAR = 1 / 60
TICK_SECONDS = 0.5
SENDER_AVATAR = {"attacker": "\U0001f575️", "customer": "\U0001f642"}
OUTCOME_TEXT = {"blocked": "✔ blocked", "leaked": "✕ leaked",
                "served": "✔ served", "refused": "⊘ refused"}
EVENT_KEYS = ("sender", "text", "reply", "zone", "outcome", "map")
GREAT_RULES_TIP = "Even great rules can fail. Real businesses should never give their chatbot secrets it does not need."
LOADED_NOTICE = "This is a replay of a saved game. Loaded games are not graded again and are never stored."
BACK_SCREEN = {"level": "level", "endless": "endless"}


# ---- playback ----------------------------------------------------------------------------------

def message_delay(event: dict, speed: str) -> float:
    """Return how many seconds to keep a message on screen: longer replies stay longer."""
    return (BASE_DELAY_SECONDS + len(event["reply"]) * SECONDS_PER_CHAR) * SPEEDS[speed]


def advance_if_due(events: list[dict]) -> None:
    """Show the next message when the current one has been on screen long enough."""
    state = st.session_state
    if not state["pb_playing"]:
        return
    if state["pb_step"] >= len(events) - 1:
        state["pb_playing"] = False
        return
    delay = message_delay(events[state["pb_step"]], state.get("pb_speed", "Normal"))
    if time.monotonic() - state["pb_last"] >= delay:
        state["pb_step"] += 1
        state["pb_last"] = time.monotonic()


def toggle_play() -> None:
    """Pause the chat, or resume it."""
    state = st.session_state
    state["pb_playing"] = not state["pb_playing"]
    state["pb_last"] = time.monotonic()


def next_message(last: int) -> None:
    """Show one more message and pause."""
    state = st.session_state
    state["pb_step"] = min(last, state["pb_step"] + 1)
    state["pb_playing"] = False


def play_all(last: int) -> None:
    """Jump to the last message."""
    st.session_state.update(pb_step=last, pb_playing=False)


def scrub() -> None:
    """Jump to the message picked on the slider and pause."""
    state = st.session_state
    state["pb_step"] = state["pb_slider"] - 1
    state["pb_playing"] = False


def show_chat(events: list[dict], step: int) -> None:
    """Show the messages up to step: customers and attackers on the left, the chatbot on the right."""
    for event in events[: step + 1]:
        left, right = st.columns(2)
        with left, st.chat_message("user", avatar=SENDER_AVATAR[event["sender"]]):
            st.text(event["text"])
        with right, st.chat_message("assistant", avatar="☕"):
            st.text(event["reply"])
            st.caption(OUTCOME_TEXT[event["outcome"]])


def show_map(zones: list[dict], event: dict) -> None:
    """Show the map as it is after this message, with the attacked zone outlined."""
    attacked = event["zone"] if event["sender"] == "attacker" else None
    common.show_svg(build_map_svg(zones, state=event["map"], attacked=attacked))


def show_controls(events: list[dict], step: int) -> None:
    """Show Pause or Resume, Next message, Play all, the speed selector and the scrubber."""
    state, last = st.session_state, len(events) - 1
    finished = step >= last
    play, nxt, every, speed = st.columns([1, 1, 1, 2])
    play.button("Pause" if state["pb_playing"] else "Resume", key="pb_toggle",
                on_click=toggle_play, disabled=finished)
    nxt.button("Next message", key="pb_next", on_click=next_message, args=(last,), disabled=finished)
    every.button("Play all", key="pb_all", on_click=play_all, args=(last,), disabled=finished)
    speed.radio("Speed", list(SPEEDS), index=1, key="pb_speed", horizontal=True)
    if last > 0:
        state["pb_slider"] = step + 1
        st.slider("Message", 1, last + 1, key="pb_slider", on_change=scrub)


@st.fragment(run_every=TICK_SECONDS)
def playback_view() -> None:
    """Chat and map for the current run. Only this part reruns on every tick, so the page stays calm."""
    run = st.session_state["run"]
    events = run["result"]["events"]
    advance_if_due(events)
    step = st.session_state["pb_step"]
    show_controls(events, step)
    chat_col, map_col = st.columns([3, 2])
    with chat_col, st.container(key="sec_chat"):
        show_chat(events, step)
    with map_col, st.container(key="sec_map"):
        show_map(common.run_source(run)["map_zones"], events[step])
    if step >= len(events) - 1 and st.button("See results", type="primary", key="pb_results"):
        common.goto("results")
        st.rerun()  # a button inside a fragment only reruns the fragment, so rerun the whole app


def playback_screen() -> None:
    """Show the chat playback of the current run."""
    run = st.session_state["run"]
    st.button("← Back", key="pb_back", on_click=common.goto, args=(BACK_SCREEN[run["mode"]],))
    st.header("Watch the round")
    playback_view()


# ---- saving and loading ------------------------------------------------------------------------

def check_events(events: object) -> list[dict]:
    """Return the events of a save, raising ValueError if they are missing or malformed."""
    if not isinstance(events, list) or not events:
        raise ValueError("This save has no messages to replay.")
    for event in events:
        if not isinstance(event, dict) or any(key not in event for key in EVENT_KEYS):
            raise ValueError("This save has malformed messages.")
        if not all(isinstance(event[key], str) for key in EVENT_KEYS[:5]) or not isinstance(event["map"], dict):
            raise ValueError("This save has malformed messages.")
        if event["sender"] not in SENDER_AVATAR or event["outcome"] not in OUTCOME_TEXT:
            raise ValueError("This save has malformed messages.")
    return events


def run_from_save(record: dict) -> dict:
    """Build a replay-only run from a parsed save file, raising ValueError if it does not fit this game."""
    result = record["result"] if isinstance(record.get("result"), dict) else record
    events = check_events(result.get("events"))
    mode = "endless" if record.get("mode") == "endless" else "level"
    scenario_id, source_id = str(record.get("scenario_id", "cafe")), str(record.get("level_id", ""))
    try:
        common.find_source(scenario_id, mode, source_id)
    except (ValueError, OSError, KeyError) as error:
        raise ValueError("This save is for a level that is not in this game.") from error
    return {"run_id": str(uuid.uuid4()), "mode": mode, "scenario_id": scenario_id, "level_id": source_id,
            "result": {"events": events}, "loaded": True, "recorded": True, "saved": False}


def load_game(key: str) -> None:
    """Read the uploaded save file and start its replay; show a message if it is not usable."""
    state = st.session_state
    uploaded = state.get(key)
    if uploaded is None:
        return
    try:
        state["run"] = run_from_save(data.import_game(uploaded.getvalue().decode("utf-8")))
    except (ValueError, UnicodeDecodeError) as error:
        state["load_error"] = str(error)
        return
    state.pop("load_error", None)
    common.start_playback()
    common.goto("playback")


def load_game_widget(key: str) -> None:
    """Show the Load my game uploader. The file is only replayed, never graded or stored."""
    st.file_uploader("Load my game", type="json", key=key, on_change=load_game, args=(key,))
    if st.session_state.get("load_error"):
        st.error(st.session_state["load_error"])


def save_record(run: dict) -> dict:
    """Return what Save my game writes: everything needed to replay the round."""
    keys = ("scenario_id", "mode", "level_id", "chosen_rules", "player_rules", "package_index", "result", "grade")
    return {key: run[key] for key in keys}


# ---- results -----------------------------------------------------------------------------------

def explain_endless(section: dict, result: dict) -> list[dict]:
    """Return one explanation per leak or refused customer of an Endless run."""
    labels = {zone["id"]: zone["label"] for zone in section["map_zones"]}
    attacks = {a["text"]: a for package in section["attack_packages"] for a in package}
    items = []
    for event in result["events"]:
        label = labels.get(event["zone"], event["zone"])
        if event["outcome"] == "leaked":
            kind = attacks.get(event["text"], {}).get("type", "unknown")
            items.append({"step": event["step"], "kind": "leak", "attack_type": kind,
                          "message": f"A {kind.replace('_', ' ')} attack made Beanie leak {label}.",
                          "caused_by_rules": [], "coach_tip": section.get("coach_tips", {}).get(kind, "")})
        elif event["outcome"] == "refused":
            items.append({"step": event["step"], "kind": "refusal",
                          "message": f"A real customer asked about {label} and did not get a helpful answer.",
                          "caused_by_rules": [], "coach_tip": data.REFUSAL_TIP})
    return items


def show_explanation(item: dict, rule_labels: dict[str, str]) -> None:
    """Show one leak or refusal with its attack type, the rule to blame and the coach tip."""
    with st.container(border=True):
        st.markdown(f"**{'Leak' if item['kind'] == 'leak' else 'Refused customer'} at message {item['step']}**")
        st.text(item["message"])
        if item.get("attack_type"):
            st.caption(f"Attack type: {item['attack_type'].replace('_', ' ')}")
        blamed = [rule_labels.get(rule_id, rule_id) for rule_id in item.get("caused_by_rules", [])]
        if blamed:
            st.write("Rule that turned them away: " + ", ".join(blamed))
        if item.get("coach_tip"):
            st.info(f"Coach tip: {item['coach_tip']}")


def show_grade(grade: dict) -> None:
    """Show the grade banner."""
    if grade["grade"] == "lose":
        st.error("The core was hacked. You lost this round.")
    elif grade["grade"] == "perfect":
        st.success(f"Perfect! {STAR * 3}")
    elif grade["grade"] == "stars":
        st.success(f"{STAR * grade['stars']} {grade['stars']} star{'s' if grade['stars'] > 1 else ''}")
    else:
        st.warning("Not enough points. Try again with different rules.")


def show_scores(run: dict, source: dict) -> None:
    """Show security, helpfulness, the penalty and the score as separate numbers."""
    grade, result = run["grade"], run["result"]
    min_rules = source.get("min_rules", 0)
    security, helpfulness = result["security"], result["helpfulness"]
    lost_points = data.penalty(result, min_rules)
    cols = st.columns(4)
    cols[0].metric("Security", f"{grade['security_pct']}%")
    cols[0].caption(f"{security['earned']}/{security['total']} points")
    cols[1].metric("Helpfulness", f"{grade['helpfulness_pct']}%")
    cols[1].caption(f"{helpfulness['earned']}/{helpfulness['total']} points")
    cols[2].metric("Penalty", f"-{lost_points}" if lost_points else "0")
    cols[3].metric("Score", grade["score"])
    st.caption("Extra rules, and written rules longer than "
               f"{data.FREE_RULES_CHARS} characters, cost points.")


def show_results_block(run: dict, source: dict) -> None:
    """Show the grade, the scores and an explanation for every leak and refusal."""
    show_grade(run["grade"])
    show_scores(run, source)
    if run["mode"] == "endless":
        st.subheader("Your rules")
        st.text(run["player_rules"] or "(no rules written)")
        items = explain_endless(source, run["result"])
    else:
        items = data.explain_result(source, run["chosen_rules"], run["result"])
    for item in items:
        show_explanation(item, {rule["id"]: rule["label"] for rule in source.get("rules", [])})
    if run["grade"]["grade"] == "perfect" or run["grade"]["stars"] == 3:
        st.info(GREAT_RULES_TIP)


def replay() -> None:
    """Play the chat and the map again from the first message."""
    common.start_playback()
    common.goto("playback")


def next_level_id(run: dict) -> str | None:
    """Return the id of the level after this one, or None."""
    levels = common.get_scenario(run["scenario_id"])["levels"]
    ids = [level["id"] for level in levels]
    index = ids.index(run["level_id"]) if run["level_id"] in ids else -1
    return ids[index + 1] if 0 <= index < len(ids) - 1 else None


def show_navigation(run: dict) -> None:
    """Show Retry, Next (or the section list) and the way back."""
    endless = run["mode"] == "endless"
    retry, onward, back = st.columns(3)
    retry.button("Retry", key="rs_retry", on_click=common.goto, args=("endless" if endless else "level",))
    if endless:
        onward.button("Other sections", key="rs_next", on_click=common.goto, args=("endless_select",))
    else:
        following = next_level_id(run)
        onward.button("Next", key="rs_next", on_click=common.open_level, args=(following,),
                      disabled=following is None or run["grade"]["stars"] < 1)
    back.button("Home", key="rs_home", on_click=common.goto, args=("home",))


def show_save_load(run: dict) -> None:
    """Show Save my game and Load my game."""
    save, load = st.columns(2)
    with save:
        st.download_button("Save my game", data=data.export_game(save_record(run)),
                           file_name=f"chatbot-defense-{run['level_id']}.json", mime="application/json",
                           key="rs_save")
    with load:
        load_game_widget("load_results")


def loaded_results(run: dict) -> None:
    """Results screen of a loaded game: replay only, no grade and no storage."""
    st.info(LOADED_NOTICE)
    replay_col, back_col = st.columns(2)
    replay_col.button("Replay", key="rs_replay", on_click=replay)
    back_col.button("Home", key="rs_home", on_click=common.goto, args=("home",))
    load_game_widget("load_results")


def results_screen() -> None:
    """Show the results of the current run."""
    run = st.session_state["run"]
    st.header("Results")
    if run["loaded"]:
        loaded_results(run)
        return
    source = common.run_source(run)
    with st.container(key="sec_results"):
        show_results_block(run, source)
    with st.container(key="sec_replay_button"):
        st.button("Replay", key="rs_replay", on_click=replay)
    with st.container(key="sec_retry_next_buttons"):
        show_navigation(run)
    show_save_load(run)
