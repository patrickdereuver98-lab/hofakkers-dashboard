"""
utils/calculations.py
Foutloze reken-engine voor het Hofakkers 44 Renovatie Dashboard.
Alle berekeningen lopen via session_state; nooit directe Excel-reads.
"""
import streamlit as st
import pandas as pd


def _safe_float(val) -> float:
    """Converteert elke waarde veilig naar float."""
    try:
        return float(val or 0)
    except (TypeError, ValueError):
        return 0.0


# ── Dashboard totalen ──────────────────────────────────────────────────────

def calculate_totals() -> dict:
    """
    Totaal budget, besteed, beschikbaar en percentage op app-niveau.
    """
    dashboard = st.session_state.get("dashboard", {})
    patrick   = _safe_float(dashboard.get("Totaal Inleg Patrick", 0))
    willianne = _safe_float(dashboard.get("Totaal Inleg Willianne", 0))
    totaal    = patrick + willianne

    # Besteed = som verbouwing + som losse kosten
    verb = st.session_state.get("verbouwing", pd.DataFrame())
    verb_sum = float(verb["Totaal (€)"].sum()) if not verb.empty and "Totaal (€)" in verb.columns else 0.0

    kosten_dict = st.session_state.get("kosten", {})
    kosten_sum  = sum(
        _safe_float(k.get("Bedrag (€)", 0))
        for items in kosten_dict.values()
        for k in items
    )
    besteed      = verb_sum + kosten_sum
    beschikbaar  = totaal - besteed
    percentage   = round(besteed / totaal * 100, 2) if totaal > 0 else 0.0

    return {
        "totaal_budget": totaal,
        "patrick":       patrick,
        "willianne":     willianne,
        "besteed":       besteed,
        "beschikbaar":   beschikbaar,
        "percentage":    percentage,
        "verb_sum":      verb_sum,
        "kosten_sum":    kosten_sum,
    }


def calculate_user_shares() -> dict:
    totals = calculate_totals()
    totaal  = totals["totaal_budget"]
    patrick = totals["patrick"]
    wil     = totals["willianne"]
    return {
        "Patrick":   {"value": patrick, "pct": round(patrick / totaal * 100, 1) if totaal else 0},
        "Willianne": {"value": wil,     "pct": round(wil     / totaal * 100, 1) if totaal else 0},
    }


# ── Per-kamer berekeningen ─────────────────────────────────────────────────

def calculate_kamer_summary(kamer: str) -> dict:
    """
    Volledige samenvatting voor één kamer:
    budget, besteed (verb + kosten), beschikbaar, voortgang taken, wensen.
    """
    from utils.state_manager import (
        get_kamer_budget, get_verbouwing_voor_kamer,
        get_kosten, get_taken, get_wensen
    )

    bud       = get_kamer_budget(kamer)
    toegewezen = bud["Toegewezen Budget (€)"]

    verb      = get_verbouwing_voor_kamer(kamer)
    verb_sum  = float(verb["Totaal (€)"].sum()) if not verb.empty and "Totaal (€)" in verb.columns else 0.0

    kosten    = get_kosten(kamer)
    kost_sum  = sum(_safe_float(k.get("Bedrag (€)", 0)) for k in kosten)

    besteed      = verb_sum + kost_sum
    beschikbaar  = toegewezen - besteed
    pct_budget   = round(besteed / toegewezen * 100, 1) if toegewezen > 0 else 0.0

    taken     = get_taken(kamer)
    gereed    = sum(1 for t in taken if t.get("Status") == "Gereed")
    bezig     = sum(1 for t in taken if t.get("Status") == "Bezig")
    todo      = sum(1 for t in taken if t.get("Status") == "Todo")
    pct_taken = round(gereed / len(taken) * 100, 1) if taken else 0.0

    wensen    = get_wensen(kamer)
    gear_wens = sum(1 for w in wensen if w.get("Status") == "Gerealiseerd")

    return {
        "kamer":         kamer,
        "toegewezen":    toegewezen,
        "besteed":       besteed,
        "beschikbaar":   beschikbaar,
        "pct_budget":    pct_budget,
        "verb_sum":      verb_sum,
        "kost_sum":      kost_sum,
        "n_taken":       len(taken),
        "n_gereed":      gereed,
        "n_bezig":       bezig,
        "n_todo":        todo,
        "pct_taken":     pct_taken,
        "n_wensen":      len(wensen),
        "n_gear_wensen": gear_wens,
    }


def calculate_all_rooms() -> list:
    """Lijst van summaries voor alle kamers."""
    rooms = st.session_state.get("rooms", [])
    return [calculate_kamer_summary(r) for r in rooms]


# ── Budget verdeling ───────────────────────────────────────────────────────

def calculate_budget_distribution() -> list:
    """
    Retourneert lijst van dicts {kamer, budget, besteed, beschikbaar}
    voor Plotly charts.
    """
    rooms = st.session_state.get("rooms", [])
    result = []
    for kamer in rooms:
        s = calculate_kamer_summary(kamer)
        if s["toegewezen"] > 0 or s["besteed"] > 0:
            result.append({
                "kamer":      kamer,
                "budget":     s["toegewezen"],
                "besteed":    s["besteed"],
                "beschikbaar": max(s["beschikbaar"], 0),
            })
    return result


# ── Verbouwing berekeningen ────────────────────────────────────────────────

def recalc_verbouwing_totalen(df: pd.DataFrame) -> pd.DataFrame:
    """
    Herbereken 'Totaal (€)' = Aantal × Kosten per eenheid.
    Veilig voor ontbrekende/lege waarden.
    """
    if df.empty:
        return df
    df = df.copy()
    if "Aantal" in df.columns and "Kosten per eenheid (€)" in df.columns:
        df["Aantal"] = pd.to_numeric(df["Aantal"], errors="coerce").fillna(0)
        df["Kosten per eenheid (€)"] = pd.to_numeric(df["Kosten per eenheid (€)"], errors="coerce").fillna(0)
        df["Totaal (€)"] = df["Aantal"] * df["Kosten per eenheid (€)"]
    return df


# ── Algehele voortgang ─────────────────────────────────────────────────────

def calculate_overall_progress() -> float:
    """Gewogen gemiddeld taakvoltooiing over alle kamers (%)."""
    rooms = st.session_state.get("rooms", [])
    if not rooms:
        return 0.0
    totaal_taken  = 0
    totaal_gereed = 0
    for kamer in rooms:
        s = calculate_kamer_summary(kamer)
        totaal_taken  += s["n_taken"]
        totaal_gereed += s["n_gereed"]
    return round(totaal_gereed / totaal_taken * 100, 1) if totaal_taken > 0 else 0.0


# ── Kosten analyse ─────────────────────────────────────────────────────────

def calculate_kosten_per_categorie() -> dict:
    """Som van kosten per categorie over alle kamers."""
    kosten_dict = st.session_state.get("kosten", {})
    result: dict = {}
    for items in kosten_dict.values():
        for k in items:
            cat   = k.get("Categorie", "Overig") or "Overig"
            bedrag = _safe_float(k.get("Bedrag (€)", 0))
            result[cat] = result.get(cat, 0) + bedrag
    return result


def calculate_kosten_timeline() -> pd.DataFrame:
    """DataFrame met datum, bedrag voor timeline chart."""
    rows = []
    kosten_dict = st.session_state.get("kosten", {})
    for kamer, items in kosten_dict.items():
        for k in items:
            datum  = str(k.get("Datum", ""))
            bedrag = _safe_float(k.get("Bedrag (€)", 0))
            if datum and bedrag > 0:
                rows.append({"Datum": datum, "Bedrag (€)": bedrag, "Kamer": kamer,
                             "Leverancier": k.get("Leverancier", "")})
    if not rows:
        return pd.DataFrame(columns=["Datum", "Bedrag (€)", "Kamer", "Leverancier"])
    df = pd.DataFrame(rows)
    df["Datum"] = pd.to_datetime(df["Datum"], errors="coerce")
    return df.sort_values("Datum").dropna(subset=["Datum"]).reset_index(drop=True)
