"""
utils/state_manager.py
Initialiseert en beheert de volledige st.session_state structuur.
Single Source of Truth via Excel; alle wijzigingen leven in session_state.
"""
import streamlit as st
import pandas as pd

from utils.excel_handler import load_all_data, save_all_data
from utils.config import DEFAULT_ROOMS


# ── Initialisatie ──────────────────────────────────────────────────────────

def init_session_state() -> None:
    """Laad Excel eenmalig in session_state bij het opstarten."""
    if st.session_state.get("_data_loaded"):
        return
    data = load_all_data()
    for key, value in data.items():
        st.session_state[key] = value
    st.session_state["_data_loaded"] = True
    _ensure_defaults()


def _ensure_defaults() -> None:
    """Zorg dat alle vereiste keys bestaan met veilige defaults."""
    st.session_state.setdefault("dashboard", {
        "Totaal Inleg Patrick": 25000,
        "Totaal Inleg Willianne": 25000,
    })
    st.session_state.setdefault("verbouwing", pd.DataFrame())
    st.session_state.setdefault("budget_verdeling", pd.DataFrame())
    st.session_state.setdefault("rooms", list(DEFAULT_ROOMS))
    st.session_state.setdefault("taken",  {r: [] for r in st.session_state["rooms"]})
    st.session_state.setdefault("kosten", {r: [] for r in st.session_state["rooms"]})
    st.session_state.setdefault("wensen", {r: [] for r in st.session_state["rooms"]})
    st.session_state.setdefault("bonnen", [])

    # Zorg dat alle kamers een lege lijst hebben
    for kamer in st.session_state["rooms"]:
        st.session_state["taken"].setdefault(kamer, [])
        st.session_state["kosten"].setdefault(kamer, [])
        st.session_state["wensen"].setdefault(kamer, [])


def reload_from_excel() -> None:
    """Forceer een herlaad vanuit Excel (reset session_state)."""
    st.session_state.pop("_data_loaded", None)
    init_session_state()


# ── Dashboard ──────────────────────────────────────────────────────────────

def get_dashboard() -> dict:
    return st.session_state.get("dashboard", {})


def get_dashboard_df() -> pd.DataFrame:
    dashboard = get_dashboard()
    return pd.DataFrame(list(dashboard.items()), columns=["Sleutel", "Waarde"])


def save_dashboard_df(df: pd.DataFrame) -> None:
    result = {}
    for _, row in df.iterrows():
        key = str(row.get("Sleutel", "")).strip()
        if key and key.lower() != "nan":
            result[key] = row.get("Waarde", 0)
    st.session_state["dashboard"] = result


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


# ── Verbouwing begroting ───────────────────────────────────────────────────

def get_verbouwing() -> pd.DataFrame:
    return st.session_state.get("verbouwing", pd.DataFrame())


def get_verbouwing_voor_kamer(kamer: str) -> pd.DataFrame:
    verb = get_verbouwing()
    if verb.empty or "Kamer" not in verb.columns:
        return pd.DataFrame()
    return verb[verb["Kamer"] == kamer].copy().reset_index(drop=True)


def save_verbouwing_voor_kamer(kamer: str, df: pd.DataFrame) -> None:
    verb = get_verbouwing()
    df = df.copy()
    df["Kamer"] = kamer
    if verb.empty or "Kamer" not in verb.columns:
        st.session_state["verbouwing"] = df
    else:
        rest = verb[verb["Kamer"] != kamer]
        st.session_state["verbouwing"] = pd.concat([rest, df], ignore_index=True)


def save_verbouwing(df: pd.DataFrame) -> None:
    st.session_state["verbouwing"] = df.copy()


# ── Budget Verdeling ───────────────────────────────────────────────────────

def get_budget_df() -> pd.DataFrame:
    return st.session_state.get("budget_verdeling", pd.DataFrame())


def save_budget_df(df: pd.DataFrame) -> None:
    st.session_state["budget_verdeling"] = df.copy()


def get_kamer_budget(kamer: str) -> dict:
    bdf = get_budget_df()
    if bdf.empty or "Kamer" not in bdf.columns:
        return {"Toegewezen Budget (€)": 0.0, "Gerealiseerd (€)": 0.0, "Beschikbaar (€)": 0.0}
    row = bdf[bdf["Kamer"] == kamer]
    if row.empty:
        return {"Toegewezen Budget (€)": 0.0, "Gerealiseerd (€)": 0.0, "Beschikbaar (€)": 0.0}
    r = row.iloc[0]
    return {
        "Toegewezen Budget (€)": float(r.get("Toegewezen Budget (€)", 0) or 0),
        "Gerealiseerd (€)":      float(r.get("Gerealiseerd (€)", 0) or 0),
        "Beschikbaar (€)":       float(r.get("Beschikbaar (€)", 0) or 0),
    }


def update_kamer_budget(kamer: str, toegewezen: float) -> None:
    bdf = get_budget_df()
    if bdf.empty or "Kamer" not in bdf.columns:
        return
    mask = bdf["Kamer"] == kamer
    if mask.any():
        bdf.loc[mask, "Toegewezen Budget (€)"] = toegewezen
        # Herbereken beschikbaar
        gerealiseerd = float(bdf.loc[mask, "Gerealiseerd (€)"].values[0] or 0)
        bdf.loc[mask, "Beschikbaar (€)"] = toegewezen - gerealiseerd
    save_budget_df(bdf)


# ── Taken ──────────────────────────────────────────────────────────────────

def get_taken(kamer: str) -> list:
    return st.session_state.get("taken", {}).get(kamer, [])


def save_taken(kamer: str, taken: list) -> None:
    if "taken" not in st.session_state:
        st.session_state["taken"] = {}
    st.session_state["taken"][kamer] = taken


def add_taak(kamer: str, taak: str, verantwoordelijke: str = "", deadline: str = "", opmerking: str = "") -> None:
    taken = get_taken(kamer)
    taken.append({
        "Taak": taak, "Status": "Todo",
        "Verantwoordelijke": verantwoordelijke,
        "Deadline": deadline, "Opmerking": opmerking,
        "Kamer": kamer,
    })
    save_taken(kamer, taken)


def update_taak_status(kamer: str, index: int, status: str) -> None:
    taken = get_taken(kamer)
    if 0 <= index < len(taken):
        taken[index]["Status"] = status
        save_taken(kamer, taken)


def delete_taak(kamer: str, index: int) -> None:
    taken = get_taken(kamer)
    if 0 <= index < len(taken):
        taken.pop(index)
        save_taken(kamer, taken)


# ── Kosten ─────────────────────────────────────────────────────────────────

def get_kosten(kamer: str) -> list:
    return st.session_state.get("kosten", {}).get(kamer, [])


def save_kosten(kamer: str, kosten: list) -> None:
    if "kosten" not in st.session_state:
        st.session_state["kosten"] = {}
    st.session_state["kosten"][kamer] = kosten


def add_kost(kamer: str, datum: str, leverancier: str, bedrag: float, categorie: str, omschrijving: str) -> None:
    kosten = get_kosten(kamer)
    kosten.append({
        "Datum": datum, "Leverancier": leverancier,
        "Bedrag (€)": bedrag, "Categorie": categorie,
        "Omschrijving": omschrijving, "Kamer": kamer,
    })
    save_kosten(kamer, kosten)
    # Update gerealiseerd in budget
    _recalc_gerealiseerd(kamer)


def delete_kost(kamer: str, index: int) -> None:
    kosten = get_kosten(kamer)
    if 0 <= index < len(kosten):
        kosten.pop(index)
        save_kosten(kamer, kosten)
        _recalc_gerealiseerd(kamer)


def _recalc_gerealiseerd(kamer: str) -> None:
    """Herbereken 'Gerealiseerd' en 'Beschikbaar' in budget_verdeling voor een kamer."""
    kosten_sum = sum(
        float(k.get("Bedrag (€)", 0) or 0)
        for k in get_kosten(kamer)
    )
    verb = get_verbouwing_voor_kamer(kamer)
    verb_sum = float(verb["Totaal (€)"].sum()) if not verb.empty and "Totaal (€)" in verb.columns else 0.0
    gerealiseerd = kosten_sum + verb_sum

    bdf = get_budget_df()
    if bdf.empty or "Kamer" not in bdf.columns:
        return
    mask = bdf["Kamer"] == kamer
    if mask.any():
        toegewezen = float(bdf.loc[mask, "Toegewezen Budget (€)"].values[0] or 0)
        bdf.loc[mask, "Gerealiseerd (€)"] = gerealiseerd
        bdf.loc[mask, "Beschikbaar (€)"]  = toegewezen - gerealiseerd
        save_budget_df(bdf)


# ── Wensen ─────────────────────────────────────────────────────────────────

def get_wensen(kamer: str) -> list:
    return st.session_state.get("wensen", {}).get(kamer, [])


def save_wensen(kamer: str, wensen: list) -> None:
    if "wensen" not in st.session_state:
        st.session_state["wensen"] = {}
    st.session_state["wensen"][kamer] = wensen


def add_wens(kamer: str, wens: str, status: str = "Idee", prioriteit: str = "Middel",
             geschat_bedrag: float = 0.0, opmerking: str = "") -> None:
    wensen = get_wensen(kamer)
    wensen.append({
        "Wens": wens, "Status": status, "Prioriteit": prioriteit,
        "Geschat Bedrag (€)": geschat_bedrag, "Opmerking": opmerking, "Kamer": kamer,
    })
    save_wensen(kamer, wensen)


def delete_wens(kamer: str, index: int) -> None:
    wensen = get_wensen(kamer)
    if 0 <= index < len(wensen):
        wensen.pop(index)
        save_wensen(kamer, wensen)


# ── Bonnen ─────────────────────────────────────────────────────────────────

def get_bonnen() -> list:
    return st.session_state.get("bonnen", [])


def add_bon(bon: dict) -> None:
    bonnen = get_bonnen()
    bonnen.append(bon)
    st.session_state["bonnen"] = bonnen


# ── Excel opslaan ──────────────────────────────────────────────────────────

def save_to_excel() -> bool:
    return save_all_data({
        "dashboard":        st.session_state.get("dashboard", {}),
        "verbouwing":       st.session_state.get("verbouwing", pd.DataFrame()),
        "budget_verdeling": st.session_state.get("budget_verdeling", pd.DataFrame()),
        "taken":            st.session_state.get("taken", {}),
        "kosten":           st.session_state.get("kosten", {}),
        "wensen":           st.session_state.get("wensen", {}),
        "bonnen":           st.session_state.get("bonnen", []),
    })
