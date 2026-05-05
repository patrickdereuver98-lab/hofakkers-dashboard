"""
utils/state.py
State management wrapper for new dashboard pages.
Bridges utils.state_manager + adds calculation functions.
"""
import streamlit as st
import pandas as pd
from utils.state_manager import (
    init_session_state, reload_from_excel, get_dashboard, 
    get_dashboard_df, save_dashboard_df, get_rooms, add_room,
    get_verbouwing, get_verbouwing_voor_kamer
)
from utils.excel_handler import load_all_data, save_all_data


# ─────────────────────────────────────────────────────────────────────────
# INITIALIZATION
# ─────────────────────────────────────────────────────────────────────────

def init() -> None:
    """Initialize session state (calls state_manager.init_session_state)."""
    init_session_state()


# ─────────────────────────────────────────────────────────────────────────
# DASHBOARD GETTERS / SETTERS
# ─────────────────────────────────────────────────────────────────────────

def dash() -> dict:
    """Get dashboard dict from session."""
    return st.session_state.get("dashboard", {})


def set_dashboard(data: dict) -> None:
    """Set dashboard dict in session."""
    st.session_state["dashboard"] = data


# ─────────────────────────────────────────────────────────────────────────
# VERBOUWING GETTERS / SETTERS
# ─────────────────────────────────────────────────────────────────────────

def verbouwing() -> pd.DataFrame:
    """Get verbouwing dataframe from session."""
    return st.session_state.get("verbouwing", pd.DataFrame())


def set_verbouwing(df: pd.DataFrame) -> None:
    """Set verbouwing dataframe in session."""
    st.session_state["verbouwing"] = df.copy()


# ─────────────────────────────────────────────────────────────────────────
# INBOEDEL GETTERS / SETTERS
# ─────────────────────────────────────────────────────────────────────────

def inboedel() -> pd.DataFrame:
    """Get inboedel dataframe from session."""
    return st.session_state.get("inboedel", pd.DataFrame())


def set_inboedel(df: pd.DataFrame) -> None:
    """Set inboedel dataframe in session."""
    st.session_state["inboedel"] = df.copy()


# ─────────────────────────────────────────────────────────────────────────
# MAAND (CASHFLOW) GETTERS / SETTERS
# ─────────────────────────────────────────────────────────────────────────

def maand() -> list:
    """Get maandelijkse begroting (list of dicts) from session."""
    return st.session_state.get("maand", [])


def set_maand(data: list) -> None:
    """Set maandelijkse begroting in session."""
    st.session_state["maand"] = data


# ─────────────────────────────────────────────────────────────────────────
# CALCULATION FUNCTIONS
# ─────────────────────────────────────────────────────────────────────────

def calc_verbouwing_totalen() -> dict:
    """
    Calculate verbouwing totals by category.
    Returns: {"categorie": {"aantal": int, "totaal": float, "count": int}, ...}
    """
    verb = verbouwing()
    if verb.empty or "Categorie" not in verb.columns:
        return {}
    
    result = {}
    for _, row in verb.iterrows():
        cat = str(row.get("Categorie", "Overig")).strip()
        if not cat or cat.lower() == "nan":
            cat = "Overig"
        
        if cat not in result:
            result[cat] = {"aantal": 0, "totaal": 0.0, "count": 0}
        
        try:
            result[cat]["aantal"] += float(row.get("Aantal", 0) or 0)
            result[cat]["totaal"] += float(row.get("Totaal (€)", 0) or 0)
            result[cat]["count"] += 1
        except (ValueError, TypeError):
            pass
    
    return result


def calc_inboedel_totalen() -> dict:
    """
    Calculate inboedel totals by category.
    Returns: {"categorie": {"aantal": int, "totaal": float, "count": int}, ...}
    """
    inb = inboedel()
    if inb.empty or "Categorie" not in inb.columns:
        return {}
    
    result = {}
    for _, row in inb.iterrows():
        cat = str(row.get("Categorie", "Overig")).strip()
        if not cat or cat.lower() == "nan":
            cat = "Overig"
        
        if cat not in result:
            result[cat] = {"aantal": 0, "totaal": 0.0, "count": 0}
        
        try:
            result[cat]["aantal"] += float(row.get("Aantal", 0) or 0)
            result[cat]["totaal"] += float(row.get("Totaal (€)", 0) or 0)
            result[cat]["count"] += 1
        except (ValueError, TypeError):
            pass
    
    return result


def calc_maand_totalen() -> dict:
    """
    Calculate monthly cashflow totals.
    Returns: {"inkomsten": float, "uitgaven": float, "sparen": float, "saldo": float}
    """
    m = maand()
    if not m:
        return {
            "inkomsten": 0.0,
            "uitgaven": 0.0,
            "sparen": 0.0,
            "saldo": 0.0,
        }
    
    inkomsten = sum(float(item.get("inkomsten", 0) or 0) for item in m)
    uitgaven = sum(float(item.get("uitgaven", 0) or 0) for item in m)
    sparen = sum(float(item.get("sparen", 0) or 0) for item in m)
    saldo = inkomsten - uitgaven
    
    return {
        "inkomsten": inkomsten,
        "uitgaven": uitgaven,
        "sparen": sparen,
        "saldo": saldo,
    }


def calc_project() -> dict:
    """
    Calculate project totals from verbouwing data.
    Returns: {"budget": float, "besteed": float, "resterend": float, "pct": float}
    """
    verb = verbouwing()
    if verb.empty:
        return {
            "budget": 0.0,
            "besteed": 0.0,
            "resterend": 0.0,
            "pct": 0.0,
        }
    
    try:
        budget = float(verb.get("Totaal (€)", 0).sum() if "Totaal (€)" in verb.columns else 0)
    except (ValueError, TypeError):
        budget = 0.0
    
    # Extract actual spent from dashboard or calculate from bonnen
    dashboard = dash()
    besteed = float(dashboard.get("Totaal Besteed", 0) or 0)
    
    resterend = budget - besteed
    pct = (besteed / max(budget, 1)) * 100 if budget > 0 else 0
    
    return {
        "budget": budget,
        "besteed": besteed,
        "resterend": resterend,
        "pct": pct,
    }


def calc_spaargeld() -> dict:
    """
    Calculate savings/vermogen for Patrick & Willianne.
    Returns: {"patrick": float, "willianne": float, "samen": float, "gespaard": float}
    """
    dashboard = dash()
    
    pat = float(dashboard.get("Totaal Inleg Patrick", 0) or 0)
    wil = float(dashboard.get("Totaal Inleg Willianne", 0) or 0)
    zusammen = pat + wil
    
    # Gespaard = total incomings - verbouwing budget
    project = calc_project()
    gespaard = zusammen - project["budget"]
    
    return {
        "patrick": pat,
        "willianne": wil,
        "samen": zusammen,
        "gespaard": max(gespaard, 0),
    }


# ─────────────────────────────────────────────────────────────────────────
# SAVE FUNCTIONS (delegates to excel_handler)
# ─────────────────────────────────────────────────────────────────────────

def save_all_to_excel() -> bool:
    """
    Save all state to Excel.
    Returns True if successful.
    """
    try:
        save_all_data()
        return True
    except Exception as e:
        st.error(f"Error saving to Excel: {e}")
        return False
