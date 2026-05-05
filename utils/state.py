"""
utils/state.py  –  Hofakkers 44
Single state layer: init, getters, setters, berekeningen.

BUGS FIXED:
- calc_verbouwing_totalen: returnt nu {"categorieën": {cat: bedrag}, "totaal": float}
- calc_inboedel_totalen:   zelfde structuur
- calc_maand_totalen:      leest correct uit maand-lijst + dashboard fallback
- calc_project:            leest verbouwing + inboedel totalen correct
- calc_spaargeld:          leest vermogenswaarden uit dashboard (echte Excel-keys)
- save_all_to_excel:       geeft session_state correct door aan save_all_data()
- sparen() / hypotheek()   toegevoegd
"""
import streamlit as st
import pandas as pd
from utils.excel_handler import load_all_data, save_all_data


# ── Initialisatie ──────────────────────────────────────────────────────────

def init() -> None:
    """Laad Excel eenmalig in session_state."""
    if st.session_state.get("_loaded"):
        return
    data = load_all_data()
    for k, v in data.items():
        st.session_state[k] = v
    st.session_state["_loaded"] = True


def reload() -> None:
    st.session_state.pop("_loaded", None)
    init()


# ── Getters ────────────────────────────────────────────────────────────────

def dash() -> dict:
    return st.session_state.get("dashboard", {})


def verbouwing() -> pd.DataFrame:
    return st.session_state.get("verbouwing", pd.DataFrame())


def inboedel() -> pd.DataFrame:
    return st.session_state.get("inboedel", pd.DataFrame())


def maand() -> list:
    return st.session_state.get("maand", [])


def sparen() -> dict:
    return st.session_state.get("sparen", {})


def hypotheek() -> dict:
    return st.session_state.get("hypotheek", {})


# ── Setters ────────────────────────────────────────────────────────────────

def set_dashboard(data: dict) -> None:
    st.session_state["dashboard"] = data


def set_verbouwing(df: pd.DataFrame) -> None:
    st.session_state["verbouwing"] = df.copy()


def set_inboedel(df: pd.DataFrame) -> None:
    st.session_state["inboedel"] = df.copy()


def set_maand(rows: list) -> None:
    st.session_state["maand"] = rows


# ── Helper ─────────────────────────────────────────────────────────────────

def _sf(v) -> float:
    try:
        return float(v or 0)
    except (TypeError, ValueError):
        return 0.0


# ── Berekeningen ───────────────────────────────────────────────────────────

def calc_verbouwing_totalen() -> dict:
    """
    Retourneert {"categorieën": {cat: totaal_bedrag, ...}, "totaal": float}.
    Gebruikt door app.py (donut chart) en 1_Verbouwing.py.
    """
    df = verbouwing()
    if df.empty or "Categorie" not in df.columns:
        return {"categorieën": {}, "totaal": 0.0}

    df = df.copy()
    df["Totaal (€)"] = pd.to_numeric(df["Totaal (€)"], errors="coerce").fillna(0)
    cats = (
        df.groupby("Categorie")["Totaal (€)"]
        .sum()
        .where(lambda x: x > 0)
        .dropna()
        .to_dict()
    )
    return {"categorieën": cats, "totaal": sum(cats.values())}


def calc_inboedel_totalen() -> dict:
    """
    Retourneert {"categorieën": {cat: totaal_bedrag, ...}, "totaal": float}.
    """
    df = inboedel()
    if df.empty or "Categorie" not in df.columns:
        return {"categorieën": {}, "totaal": 0.0}

    df = df.copy()
    df["Totaal (€)"] = pd.to_numeric(df["Totaal (€)"], errors="coerce").fillna(0)
    cats = (
        df.groupby("Categorie")["Totaal (€)"]
        .sum()
        .where(lambda x: x > 0)
        .dropna()
        .to_dict()
    )
    return {"categorieën": cats, "totaal": sum(cats.values())}


def calc_maand_totalen() -> dict:
    """
    Retourneert cashflow-samenvatting:
    {inkomen, vaste, variabel, sparen, ruimte, totaal_uitgaven}

    Primaire bron: Dashboard PRO (exacte keys uit de echte Excel).
    Fallback: aggregatie van maand-lijst als Dashboard leeg is.
    """
    d = dash()

    # ── Primaire bron: Dashboard PRO ──
    inkomen  = _sf(d.get("Netto inkomen per maand"))
    vaste    = _sf(d.get("Vaste lasten per maand (wonen + verzekeringen + vervoer)"))
    variabel = _sf(d.get("Variabele lasten per maand (boodschappen + vrijetijd)"))
    spar     = _sf(d.get("Sparen & beleggen per maand"))

    # Als dashboard leeg is, aggregeer uit maand-lijst
    if inkomen == 0:
        rows = maand()
        for row in rows:
            cat = str(row.get("Categorie", "")).upper()
            bedrag = _sf(row.get("Bedrag (€)") or row.get("bedrag"))
            if "INKOMST" in cat:
                inkomen += bedrag
            elif cat in ("WONEN", "VERZEKERING", "VERVOER", "VASTE"):
                vaste += bedrag
            elif cat in ("BOODSCHAP", "VARIABEL", "PERSOONLIJK", "VRIJETIJD", "HUISHOUD"):
                variabel += bedrag
            elif "SPAR" in cat or "BELEGG" in cat:
                spar += bedrag

    totaal_uitgaven = vaste + variabel + spar
    ruimte = inkomen - totaal_uitgaven

    return {
        "inkomen":         inkomen,
        "vaste":           vaste,
        "variabel":        variabel,
        "sparen":          spar,
        "ruimte":          ruimte,
        "totaal_uitgaven": totaal_uitgaven,
    }


def calc_project() -> dict:
    """
    Project-totalen:
    {verbouwing, inboedel, project, per_persoon, samen, patrick, willianne}

    Primaire bron: berekend uit verbouwing/inboedel DataFrames.
    Overrides: uit Dashboard PRO als die er zijn.
    """
    d = dash()

    vt = calc_verbouwing_totalen()
    it = calc_inboedel_totalen()

    verb_calc  = vt["totaal"]
    inbo_calc  = it["totaal"]

    # Dashboard kan override bevatten
    verb_tot   = _sf(d.get("Verbouwing (totaal)")) or verb_calc
    inbo_tot   = _sf(d.get("Inboedel (totaal)"))   or inbo_calc
    project    = verb_tot + inbo_tot

    per_persoon = _sf(d.get("Benodigd per persoon")) or (project / 2 if project else 0)
    samen       = _sf(d.get("Samen vermogen na verbouwing"))
    patrick     = _sf(d.get("Vermogen Patrick na verbouwing"))
    willianne   = _sf(d.get("Vermogen Willianne na verbouwing"))

    return {
        "verbouwing":  verb_tot,
        "inboedel":    inbo_tot,
        "project":     project,
        "per_persoon": per_persoon,
        "samen":       samen,
        "patrick":     patrick,
        "willianne":   willianne,
    }


def calc_spaargeld() -> dict:
    """
    Vermogensoverzicht Patrick & Willianne.
    Leest uitsluitend uit Dashboard PRO (echte Excel-keys).
    """
    d = dash()
    patrick   = _sf(d.get("Vermogen Patrick na verbouwing"))
    willianne = _sf(d.get("Vermogen Willianne na verbouwing"))
    samen     = _sf(d.get("Samen vermogen na verbouwing")) or (patrick + willianne)
    gespaard  = _sf(d.get("Totaal sparen + beleggen nu"))

    return {
        "patrick":       patrick,
        "willianne":     willianne,
        "samen":         samen,
        "totaal_sparen": gespaard,
    }


# ── Excel opslaan ──────────────────────────────────────────────────────────

def save_all_to_excel() -> bool:
    """Schrijf volledige session_state terug naar Excel."""
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
