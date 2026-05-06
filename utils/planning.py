"""
utils/planning.py  –  Hofakkers 44  v4.0

Planning state management.
Initialiseert een standaard planning op basis van verbouwingscategorieën.
Biedt CRUD + herschikken van planningsstappen.
"""
import streamlit as st
import pandas as pd
from datetime import date, timedelta


# ── Kolom definitie ────────────────────────────────────────────────────────
PLAN_COLS = [
    "Volgorde", "Taak", "Categorie", "Verantwoordelijke",
    "Startdatum", "Deadline", "Status", "Prioriteit",
    "Afhankelijk_Van", "Budget_Ref", "Notities",
]

STATUSSEN   = ["Gepland", "Gestart", "In uitvoering", "Wacht op ander", "Gereed", "On hold"]
PRIORITEITEN = ["Laag", "Normaal", "Hoog", "Urgent"]

STATUS_COLORS = {
    "Gepland":        "#6B7280",
    "Gestart":        "#3B82F6",
    "In uitvoering":  "#F59E0B",
    "Wacht op ander": "#8B5CF6",
    "Gereed":         "#10B981",
    "On hold":        "#EF4444",
}

STATUS_ICONS = {
    "Gepland":        "⚪",
    "Gestart":        "🔵",
    "In uitvoering":  "🟡",
    "Wacht op ander": "🟣",
    "Gereed":         "🟢",
    "On hold":        "🔴",
}

PRIO_ICONS = {
    "Laag":   "🟢",
    "Normaal": "🔵",
    "Hoog":   "🟡",
    "Urgent": "🔴",
}


# ── Standaard planning (vanuit verbouwingsvolgorde) ────────────────────────

_DEFAULT_PLANNING = [
    # (Taak, Categorie, Verantwoordelijke, offset_start_dagen, duur_dagen, afh_van)
    ("Sloop & voorbereiding",      "Uitbouw",                    "Patrick",          0,  14, ""),
    ("Fundering uitbouw",          "Uitbouw",                    "Aannemer",         14, 10, "Sloop & voorbereiding"),
    ("Uitbouw casco bouwen",       "Uitbouw",                    "Aannemer",         24, 21, "Fundering uitbouw"),
    ("Elektrische vloerverwarming","Vloeren & vloerverwarming",  "Installateur",     45,  5, "Uitbouw casco bouwen"),
    ("Vloer leggen begane grond",  "Vloeren & vloerverwarming",  "Vloerlegger",      50,  4, "Elektrische vloerverwarming"),
    ("Plinten & afwerking vloer",  "Vloeren & vloerverwarming",  "Patrick",          54,  2, "Vloer leggen begane grond"),
    ("Leidingen keuken aanpassen", "Keuken met kookeiland",      "Loodgieter",       45,  3, "Uitbouw casco bouwen"),
    ("Elektra keuken aanleggen",   "Keuken met kookeiland",      "Elektricien",      48,  3, "Leidingen keuken aanpassen"),
    ("Keuken plaatsen",            "Keuken met kookeiland",      "Keukenmonteur",    60, 10, "Vloer leggen begane grond"),
    ("Badkamer sloopwerk",         "Badkamer & toilet",          "Patrick",           0,  3, ""),
    ("Tegelwerk badkamer",         "Badkamer & toilet",          "Tegelzetter",      30, 7,  "Badkamer sloopwerk"),
    ("Sanitair plaatsen",          "Badkamer & toilet",          "Loodgieter",       38, 3,  "Tegelwerk badkamer"),
    ("Grondverf & voorbereiden",   "Schilder- en behangwerk binnen","Patrick",       54,  3, "Vloer leggen begane grond"),
    ("Schilderwerk muren/plafond", "Schilder- en behangwerk binnen","Schilder",      57,  7, "Grondverf & voorbereiden"),
    ("Behang aanbrengen",          "Schilder- en behangwerk binnen","Patrick",       64,  4, "Schilderwerk muren/plafond"),
    ("Verlichting installeren",    "Overig & reserve",           "Elektricien",      70,  3, "Keuken plaatsen"),
    ("Kleine materialen & afwerking","Overig & reserve",         "Patrick",          73,  5, "Verlichting installeren"),
    ("Eindoplevering & inspectie", "Overig & reserve",           "Patrick & Willianne",78, 1, "Kleine materialen & afwerking"),
]


def _get_today() -> date:
    return date.today()


def init_planning() -> None:
    """
    Initialiseer planning in session_state als die er nog niet is.
    Volgorde: ① al in session_state → return. ② Excel heeft Planning-sheet → laad die.
    ③ Geen Excel-data → gebruik de 18 standaard-stappen.
    Planning gaat nooit meer verloren bij herstart.
    """
    if "planning" in st.session_state and st.session_state["planning"]:
        return

    # Probeer eerst uit Excel te laden
    planning_from_excel = load_planning_from_excel()
    if planning_from_excel:
        st.session_state["planning"] = planning_from_excel
        return

    # Anders: defaults
    today   = _get_today()
    planning = []
    for i, (taak, cat, verant, offset_s, duur, afh) in enumerate(_DEFAULT_PLANNING):
        start = today + timedelta(days=offset_s)
        eind  = start + timedelta(days=duur)
        planning.append({
            "Volgorde":        i + 1,
            "Taak":            taak,
            "Categorie":       cat,
            "Verantwoordelijke": verant,
            "Startdatum":      str(start),
            "Deadline":        str(eind),
            "Status":          "Gepland",
            "Prioriteit":      "Normaal",
            "Afhankelijk_Van": afh,
            "Budget_Ref":      cat,
            "Notities":        "",
        })

    st.session_state["planning"] = planning


def get_planning() -> list[dict]:
    init_planning()
    return st.session_state.get("planning", [])


def save_planning(planning: list[dict]) -> None:
    """Sla planning op in session_state én Excel."""
    st.session_state["planning"] = planning
    _save_to_excel(planning)


def _save_to_excel(planning: list[dict]) -> bool:
    """Schrijf planning naar een apart tabblad in de Excel."""
    try:
        from utils.excel_handler import _open_wb, _write_sheet, _atomic_save
        if not planning:
            return True
        df  = pd.DataFrame(planning)
        wb  = _open_wb()
        if wb is None:
            return False
        _write_sheet(wb, "Planning", df)
        return _atomic_save(wb)
    except Exception:
        return False


def load_planning_from_excel() -> list[dict]:
    """Probeer bestaande planning uit Excel te laden."""
    try:
        from utils.excel_handler import _get_sheets
        sheets = _get_sheets()
        df = sheets.get("Planning")
        if df is None or df.empty:
            return []
        # Controleer of rij 0 de header is
        if str(df.iloc[0, 0]).strip().lower() == "volgorde":
            df.columns = [str(c).strip() for c in df.iloc[0]]
            df = df.iloc[1:].reset_index(drop=True)
        else:
            df.columns = [str(c).strip() for c in df.columns]
        rows = []
        for _, row in df.iterrows():
            item = {}
            for col in PLAN_COLS:
                item[col] = row.get(col, "") if col in df.columns else ""
            rows.append(item)
        return rows
    except Exception:
        return []


# ── Herschikken (drag & drop logica) ──────────────────────────────────────

def move_up(index: int) -> None:
    """Verplaats een stap één positie omhoog."""
    planning = get_planning()
    if index <= 0 or index >= len(planning):
        return
    planning[index-1], planning[index] = planning[index], planning[index-1]
    _renumber(planning)
    save_planning(planning)


def move_down(index: int) -> None:
    """Verplaats een stap één positie omlaag."""
    planning = get_planning()
    if index < 0 or index >= len(planning) - 1:
        return
    planning[index], planning[index+1] = planning[index+1], planning[index]
    _renumber(planning)
    save_planning(planning)


def move_to_position(from_idx: int, to_idx: int) -> None:
    """Verplaats stap van positie from_idx naar to_idx."""
    planning = get_planning()
    if from_idx < 0 or from_idx >= len(planning):
        return
    if to_idx < 0 or to_idx >= len(planning):
        return
    item = planning.pop(from_idx)
    planning.insert(to_idx, item)
    _renumber(planning)
    save_planning(planning)


def add_stap(taak: str, categorie: str, verant: str,
             start: str, deadline: str, status: str,
             prioriteit: str, afh: str, notities: str) -> None:
    planning = get_planning()
    planning.append({
        "Volgorde":          len(planning) + 1,
        "Taak":              taak,
        "Categorie":         categorie,
        "Verantwoordelijke": verant,
        "Startdatum":        start,
        "Deadline":          deadline,
        "Status":            status,
        "Prioriteit":        prioriteit,
        "Afhankelijk_Van":   afh,
        "Budget_Ref":        categorie,
        "Notities":          notities,
    })
    _renumber(planning)
    save_planning(planning)


def delete_stap(index: int) -> None:
    planning = get_planning()
    if 0 <= index < len(planning):
        planning.pop(index)
        _renumber(planning)
        save_planning(planning)


def update_status(index: int, status: str) -> None:
    planning = get_planning()
    if 0 <= index < len(planning):
        planning[index]["Status"] = status
        save_planning(planning)


def _renumber(planning: list[dict]) -> None:
    for i, stap in enumerate(planning):
        stap["Volgorde"] = i + 1


# ── Statistieken ──────────────────────────────────────────────────────────

def get_planning_stats() -> dict:
    planning = get_planning()
    if not planning:
        return {"totaal":0,"gereed":0,"bezig":0,"gepland":0,"onhold":0,"pct":0.0}
    totaal  = len(planning)
    gereed  = sum(1 for p in planning if p["Status"] == "Gereed")
    bezig   = sum(1 for p in planning if p["Status"] in ("In uitvoering","Gestart"))
    gepland = sum(1 for p in planning if p["Status"] == "Gepland")
    onhold  = sum(1 for p in planning if p["Status"] == "On hold")
    return {
        "totaal":  totaal,
        "gereed":  gereed,
        "bezig":   bezig,
        "gepland": gepland,
        "onhold":  onhold,
        "pct":     round(gereed / totaal * 100, 1) if totaal else 0.0,
    }


def get_gantt_data() -> pd.DataFrame:
    """DataFrame geschikt voor een Plotly Gantt chart."""
    planning = get_planning()
    rows = []
    for p in planning:
        try:
            start_d = date.fromisoformat(str(p.get("Startdatum","")))
            end_d   = date.fromisoformat(str(p.get("Deadline","")))
        except ValueError:
            continue
        rows.append({
            "Task":     p["Taak"],
            "Start":    start_d,
            "Finish":   end_d,
            "Resource": p["Categorie"],
            "Status":   p["Status"],
            "Prio":     p["Prioriteit"],
        })
    df = pd.DataFrame(rows) if rows else pd.DataFrame(
        columns=["Task","Start","Finish","Resource","Status","Prio"])
    # Converteer naar datetime voor Plotly vline() compatibility
    if not df.empty:
        df["Start"] = pd.to_datetime(df["Start"])
        df["Finish"] = pd.to_datetime(df["Finish"])
    return df
