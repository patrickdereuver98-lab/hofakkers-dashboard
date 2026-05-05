"""
utils/state_manager.py  –  Hofakkers 44
Lage-niveau state CRUD (taken, kosten, wensen, budget).
Initialisatie delegeert aan utils/state.py via load_all_data().

BUGS FIXED:
- init_session_state: laadt inboedel en maand ook correct
- save_to_excel: geeft volledige state correct door
"""
import streamlit as st
import pandas as pd

from utils.excel_handler import load_all_data, save_all_data
from utils.config import DEFAULT_ROOMS


def init_session_state() -> None:
    if st.session_state.get("_data_loaded"):
        return
    data = load_all_data()
    for key, value in data.items():
        st.session_state[key] = value
    st.session_state["_data_loaded"] = True
    _ensure_defaults()


def _ensure_defaults() -> None:
    st.session_state.setdefault("dashboard",  {})
    st.session_state.setdefault("verbouwing", pd.DataFrame())
    st.session_state.setdefault("inboedel",   pd.DataFrame())
    st.session_state.setdefault("maand",      [])
    st.session_state.setdefault("rooms",      list(DEFAULT_ROOMS))
    st.session_state.setdefault("taken",      {r: [] for r in st.session_state["rooms"]})
    st.session_state.setdefault("kosten",     {r: [] for r in st.session_state["rooms"]})
    st.session_state.setdefault("wensen",     {r: [] for r in st.session_state["rooms"]})
    st.session_state.setdefault("bonnen",     [])
    for kamer in st.session_state["rooms"]:
        st.session_state["taken"].setdefault(kamer, [])
        st.session_state["kosten"].setdefault(kamer, [])
        st.session_state["wensen"].setdefault(kamer, [])


def reload_from_excel() -> None:
    st.session_state.pop("_data_loaded", None)
    init_session_state()


# ── Dashboard ──────────────────────────────────────────────────────────────

def get_dashboard() -> dict:
    return st.session_state.get("dashboard", {})


def get_dashboard_df() -> pd.DataFrame:
    return pd.DataFrame(list(get_dashboard().items()), columns=["Sleutel", "Waarde"])


def save_dashboard_df(df: pd.DataFrame) -> None:
    result = {}
    for _, row in df.iterrows():
        key = str(row.get("Sleutel", "")).strip()
        if key and key.lower() != "nan":
            result[key] = row.get("Waarde", 0)
    st.session_state["dashboard"] = result


# ── Verbouwing ─────────────────────────────────────────────────────────────

def get_verbouwing() -> pd.DataFrame:
    return st.session_state.get("verbouwing", pd.DataFrame())


def get_verbouwing_voor_kamer(kamer: str) -> pd.DataFrame:
    verb = get_verbouwing()
    if verb.empty or "Kamer" not in verb.columns:
        return pd.DataFrame()
    return verb[verb["Kamer"] == kamer].copy().reset_index(drop=True)


# ── Rooms ──────────────────────────────────────────────────────────────────

def get_rooms() -> list:
    return st.session_state.get("rooms", list(DEFAULT_ROOMS))


def add_room(naam: str) -> None:
    rooms = get_rooms()
    if naam and naam not in rooms:
        rooms.append(naam)
        st.session_state["rooms"] = sorted(rooms)
        st.session_state["taken"].setdefault(naam, [])
        st.session_state["kosten"].setdefault(naam, [])
        st.session_state["wensen"].setdefault(naam, [])


# ── Taken ──────────────────────────────────────────────────────────────────

def get_taken(kamer: str) -> list:
    return st.session_state.get("taken", {}).get(kamer, [])


def save_taken(kamer: str, taken: list) -> None:
    st.session_state.setdefault("taken", {})[kamer] = taken


def delete_taak(kamer: str, index: int) -> None:
    taken = get_taken(kamer)
    if 0 <= index < len(taken):
        taken.pop(index)
        save_taken(kamer, taken)


# ── Kosten ─────────────────────────────────────────────────────────────────

def get_kosten(kamer: str) -> list:
    return st.session_state.get("kosten", {}).get(kamer, [])


def save_kosten(kamer: str, kosten: list) -> None:
    st.session_state.setdefault("kosten", {})[kamer] = kosten


def _recalc_gerealiseerd(kamer: str) -> None:
    pass  # Budget-verdeling sheet niet meer gebruikt in v2; placeholder


def delete_kost(kamer: str, index: int) -> None:
    kosten = get_kosten(kamer)
    if 0 <= index < len(kosten):
        kosten.pop(index)
        save_kosten(kamer, kosten)


# ── Wensen ─────────────────────────────────────────────────────────────────

def get_wensen(kamer: str) -> list:
    return st.session_state.get("wensen", {}).get(kamer, [])


def save_wensen(kamer: str, wensen: list) -> None:
    st.session_state.setdefault("wensen", {})[kamer] = wensen


def delete_wens(kamer: str, index: int) -> None:
    wensen = get_wensen(kamer)
    if 0 <= index < len(wensen):
        wensen.pop(index)
        save_wensen(kamer, wensen)


# ── Bonnen ─────────────────────────────────────────────────────────────────

def get_bonnen() -> list:
    return st.session_state.get("bonnen", [])


def add_bon(bon: dict) -> None:
    st.session_state.setdefault("bonnen", []).append(bon)


# ── Excel opslaan ──────────────────────────────────────────────────────────

def save_to_excel() -> bool:
    return save_all_data({
        "dashboard":  st.session_state.get("dashboard", {}),
        "verbouwing": st.session_state.get("verbouwing", pd.DataFrame()),
        "inboedel":   st.session_state.get("inboedel",   pd.DataFrame()),
        "maand":      st.session_state.get("maand",      []),
        "taken":      st.session_state.get("taken",      {}),
        "kosten":     st.session_state.get("kosten",     {}),
        "wensen":     st.session_state.get("wensen",     {}),
        "bonnen":     st.session_state.get("bonnen",     []),
    })
