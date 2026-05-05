"""
utils/excel_handler.py
Robuuste Excel I/O voor het Hofakkers 44 Renovatie Dashboard.
Single Source of Truth: Begroting_Willianne_Patrick_PRO_v2.xlsx
"""
import streamlit as st
import pandas as pd
import openpyxl
from openpyxl.utils.dataframe import dataframe_to_rows
from pathlib import Path

from utils.config import (
    EXCEL_FILE, DEFAULT_ROOMS, TASK_STATUSES, WISH_STATUSES,
)

# ── Verwachte kolommen per sheet ───────────────────────────────────────────
VERB_COLS  = ["Categorie", "Post", "Aantal", "Eenheid",
              "Kosten per eenheid (€)", "Totaal (€)", "Opmerking", "Kamer"]
INBOEDEL_COLS = ["Categorie", "Post", "Aantal", "Eenheid",
                 "Kosten per eenheid (€)", "Totaal (€)", "Opmerking", "Kamer"]
MAAND_COLS = ["Maand", "Inkomsten", "Uitgaven", "Sparen", "Saldo"]
TAKEN_COLS  = ["Kamer", "Taak", "Status", "Verantwoordelijke", "Deadline", "Opmerking"]
KOSTEN_COLS = ["Kamer", "Datum", "Leverancier", "Bedrag (€)", "Categorie", "Omschrijving"]
WENSEN_COLS = ["Kamer", "Wens", "Status", "Prioriteit", "Geschat Bedrag (€)", "Opmerking"]
BONNEN_COLS = ["Datum", "Leverancier", "Bedrag (€)", "Categorie", "Kamer", "Omschrijving", "BTW (€)"]
BUDGET_COLS = ["Kamer", "Toegewezen Budget (€)", "Gerealiseerd (€)", "Beschikbaar (€)"]


def file_exists() -> bool:
    return EXCEL_FILE.exists()


def _safe_read_excel() -> dict:
    """Laad alle sheets als {naam: DataFrame}."""
    try:
        return pd.read_excel(EXCEL_FILE, sheet_name=None, engine="openpyxl")
    except Exception as exc:
        raise RuntimeError(f"Kon Excel niet lezen: {exc}") from exc


def _norm_cols(df: pd.DataFrame) -> pd.DataFrame:
    """Strip whitespace van kolomnamen."""
    df = df.copy()
    df.columns = [str(c).strip() for c in df.columns]
    return df


def _ensure_cols(df: pd.DataFrame, cols: list, defaults: dict = None) -> pd.DataFrame:
    """Voeg ontbrekende kolommen toe met default waarden."""
    defaults = defaults or {}
    for c in cols:
        if c not in df.columns:
            df[c] = defaults.get(c, "")
    return df[cols].copy()


def _map_section_to_room(section: str) -> str:
    """Converteer een begrotingssectie naar een geschatte kamernaam."""
    if not isinstance(section, str):
        return "Algemeen"
    label = section.lower()
    if "keuken" in label:
        return "Keuken"
    if "badkamer" in label or "toilet" in label or "sanitair" in label:
        return "Badkamer"
    if "woonkamer" in label:
        return "Woonkamer"
    if "woon/keuken" in label or "woonkamer/keuken" in label or "woon keuken" in label:
        return "Woonkamer"
    if "uitbouw" in label or "vloeren" in label or "vloer" in label or "schilder" in label or "verf" in label:
        return "Woonkamer"
    if "hal" in label and "schilder" not in label:
        return "Hal"
    if "tuin" in label:
        return "Tuin"
    if "garage" in label:
        return "Garage"
    if "zolder" in label:
        return "Zolder"
    if "kelder" in label:
        return "Kelder"
    if any(x in label for x in ["overig", "reserve", "algemeen"]):
        return "Algemeen"
    return "Algemeen"


# ── Loaders ────────────────────────────────────────────────────────────────

def _load_dashboard(df: pd.DataFrame) -> dict:
    if df is None or df.empty:
        return {"Totaal Inleg Patrick": 25000, "Totaal Inleg Willianne": 25000}
    df = _norm_cols(df)
    if df.shape[1] < 2:
        return {}
    result = {}
    for _, row in df.iterrows():
        key = str(row.iloc[0]).strip()
        if key and key.lower() != "nan":
            val = row.iloc[1]
            result[key] = val if not pd.isna(val) else 0
    return result


def _load_verbouwing(df: pd.DataFrame) -> pd.DataFrame:
    if df is None or df.empty:
        return pd.DataFrame(columns=VERB_COLS)

    # Zorg dat de juiste headerrij wordt gebruikt voor deze sheet.
    if "Categorie" not in df.columns:
        try:
            df = pd.read_excel(EXCEL_FILE, sheet_name="Verbouwing begroting", header=1, engine="openpyxl")
        except Exception:
            df = _norm_cols(df)
    else:
        df = _norm_cols(df)

    df = _ensure_cols(df, VERB_COLS[:-1], {"Aantal": 0, "Kosten per eenheid (€)": 0.0, "Totaal (€)": 0.0})
    df["Kamer"] = "Algemeen"

    current_section = "Algemeen"
    rows = []
    for _, row in df.iterrows():
        categorie = row["Categorie"]
        post = row["Post"]
        aantal = row["Aantal"]
        eenheid = row["Eenheid"]
        kosten_per = row["Kosten per eenheid (€)"]
        totaal = row["Totaal (€)"]
        opmerking = row["Opmerking"]

        if pd.isna(post) and isinstance(categorie, str) and categorie.strip():
            label = categorie.strip()
            lower = label.lower()
            if "totale" in lower or "totaal" in lower or "totaal" == lower:
                continue
            if pd.isna(aantal) and pd.isna(eenheid) and (pd.isna(kosten_per) or isinstance(kosten_per, str)):
                current_section = label
                continue
            if isinstance(kosten_per, str) and "totaal" in kosten_per.lower():
                continue

        if pd.isna(post) or str(post).strip().lower() == "nan":
            continue

        kamer = _map_section_to_room(current_section)
        aantal = float(aantal or 0)
        kosten_per = float(kosten_per or 0)
        totaal = float(totaal or (aantal * kosten_per))

        rows.append({
            "Categorie": str(categorie).strip() if not pd.isna(categorie) else "",
            "Post": str(post).strip(),
            "Aantal": aantal,
            "Eenheid": str(eenheid).strip() if not pd.isna(eenheid) else "",
            "Kosten per eenheid (€)": kosten_per,
            "Totaal (€)": totaal,
            "Opmerking": str(opmerking).strip() if not pd.isna(opmerking) else "",
            "Kamer": kamer,
        })

    if not rows:
        return pd.DataFrame(columns=VERB_COLS)

    result = pd.DataFrame(rows, columns=VERB_COLS)
    return result.reset_index(drop=True)


def _derive_budget_from_verbouwing(df: pd.DataFrame, rooms: list) -> pd.DataFrame:
    totals = df.groupby("Kamer")["Totaal (€)"].sum().reindex(rooms, fill_value=0.0).reset_index()
    totals["Toegewezen Budget (€)"] = totals["Totaal (€)"].astype(float)
    totals["Gerealiseerd (€)"] = 0.0
    totals["Beschikbaar (€)"] = totals["Toegewezen Budget (€)"]
    return totals[["Kamer", "Toegewezen Budget (€)", "Gerealiseerd (€)", "Beschikbaar (€)"]].copy()


def _load_budget(df: pd.DataFrame, rooms: list, verb_df: pd.DataFrame) -> pd.DataFrame:
    if df is None or df.empty:
        return _derive_budget_from_verbouwing(verb_df, rooms)
    df = _norm_cols(df)
    df = _ensure_cols(df, BUDGET_COLS, {"Toegewezen Budget (€)": 0.0, "Gerealiseerd (€)": 0.0, "Beschikbaar (€)": 0.0})
    df["Kamer"] = df["Kamer"].fillna("Algemeen").astype(str).str.strip()
    for col in ["Toegewezen Budget (€)", "Gerealiseerd (€)", "Beschikbaar (€)"]:
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0.0)
    bestaande = df["Kamer"].tolist()
    extra = [r for r in rooms if r not in bestaande]
    if extra:
        df = pd.concat([df, pd.DataFrame({
            "Kamer": extra,
            "Toegewezen Budget (€)": 0.0,
            "Gerealiseerd (€)":       0.0,
            "Beschikbaar (€)":        0.0,
        })], ignore_index=True)
    return df.reset_index(drop=True)


def _load_room_list(df: pd.DataFrame, cols: list) -> dict:
    """Laad een sheet met een 'Kamer' kolom naar {kamer: [dict, ...]}.
    Ontbrekende kolommen worden aangevuld met lege strings."""
    result: dict = {}
    if df is None or df.empty:
        return result
    df = _norm_cols(df)
    df = _ensure_cols(df, cols)
    df["Kamer"] = df["Kamer"].fillna("Algemeen").astype(str).str.strip()
    for _, row in df.iterrows():
        kamer = row["Kamer"]
        item = {c: row[c] for c in cols if c != "Kamer"}
        # Vervang NaN door lege string / 0
        for k, v in item.items():
            if isinstance(v, float) and pd.isna(v):
                item[k] = ""
        item["Kamer"] = kamer
        result.setdefault(kamer, []).append(item)
    return result


def _load_bonnen(df: pd.DataFrame) -> list:
    if df is None or df.empty:
        return []
    df = _norm_cols(df)
    df = _ensure_cols(df, BONNEN_COLS)
    return df.to_dict(orient="records")


def _load_inboedel(df: pd.DataFrame) -> pd.DataFrame:
    """Load inboedel begroting sheet."""
    if df is None or df.empty:
        return pd.DataFrame(columns=INBOEDEL_COLS)
    
    df = _norm_cols(df)
    df = _ensure_cols(df, INBOEDEL_COLS[:-1], {"Aantal": 0, "Kosten per eenheid (€)": 0.0, "Totaal (€)": 0.0})
    df["Kamer"] = "Algemeen"
    
    current_section = "Algemeen"
    rows = []
    for _, row in df.iterrows():
        categorie = row["Categorie"]
        post = row["Post"]
        aantal = row["Aantal"]
        eenheid = row["Eenheid"]
        kosten_per = row["Kosten per eenheid (€)"]
        totaal = row["Totaal (€)"]
        opmerking = row["Opmerking"]
        
        if pd.isna(post) and isinstance(categorie, str) and categorie.strip():
            label = categorie.strip()
            lower = label.lower()
            if "totale" in lower or "totaal" in lower or "totaal" == lower:
                continue
            if pd.isna(aantal) and pd.isna(eenheid) and (pd.isna(kosten_per) or isinstance(kosten_per, str)):
                current_section = label
                continue
            if isinstance(kosten_per, str) and "totaal" in kosten_per.lower():
                continue
        
        if pd.isna(post) or str(post).strip().lower() == "nan":
            continue
        
        kamer = _map_section_to_room(current_section)
        aantal = float(aantal or 0)
        kosten_per = float(kosten_per or 0)
        totaal = float(totaal or (aantal * kosten_per))
        
        rows.append({
            "Categorie": str(categorie).strip() if not pd.isna(categorie) else "",
            "Post": str(post).strip(),
            "Aantal": aantal,
            "Eenheid": str(eenheid).strip() if not pd.isna(eenheid) else "",
            "Kosten per eenheid (€)": kosten_per,
            "Totaal (€)": totaal,
            "Opmerking": str(opmerking).strip() if not pd.isna(opmerking) else "",
            "Kamer": kamer,
        })
    
    if not rows:
        return pd.DataFrame(columns=INBOEDEL_COLS)
    
    result = pd.DataFrame(rows, columns=INBOEDEL_COLS)
    return result.reset_index(drop=True)


def _load_maand(df: pd.DataFrame) -> list:
    """Load maandelijkse begroting sheet."""
    if df is None or df.empty:
        return []
    
    df = _norm_cols(df)
    df = _ensure_cols(df, MAAND_COLS, {"Inkomsten": 0.0, "Uitgaven": 0.0, "Sparen": 0.0, "Saldo": 0.0})
    
    result = []
    for _, row in df.iterrows():
        result.append({
            "Maand": str(row.get("Maand", "")).strip(),
            "Inkomsten": float(row.get("Inkomsten", 0) or 0),
            "Uitgaven": float(row.get("Uitgaven", 0) or 0),
            "Sparen": float(row.get("Sparen", 0) or 0),
            "Saldo": float(row.get("Saldo", 0) or 0),
        })
    
    return result


# ── Hoofd-loader ───────────────────────────────────────────────────────────

def load_all_data() -> dict:
    """
    Laad alle sheets uit de Excel en retourneer een dict klaar voor session_state.
    Fouttolerant: ontbrekende sheets/kolommen worden aangevuld met defaults.
    """
    if not file_exists():
        st.error(f"Excel bestand niet gevonden: {EXCEL_FILE}")
        return _empty_state()

    try:
        sheets = _safe_read_excel()
    except RuntimeError as exc:
        st.error(str(exc))
        return _empty_state()

    verbouwing  = _load_verbouwing(sheets.get("Verbouwing begroting"))
    rooms_excel = sorted(verbouwing["Kamer"].dropna().unique().tolist())
    rooms       = sorted(set(rooms_excel) | set(DEFAULT_ROOMS))

    taken  = _load_room_list(sheets.get("Taken"),  TAKEN_COLS)
    kosten = _load_room_list(sheets.get("Kosten"), KOSTEN_COLS)
    wensen = _load_room_list(sheets.get("Wensen"), WENSEN_COLS)

    # Zorg dat elke kamer een lege lijst heeft
    for kamer in rooms:
        taken.setdefault(kamer, [])
        kosten.setdefault(kamer, [])
        wensen.setdefault(kamer, [])

    return {
        "dashboard":       _load_dashboard(sheets.get("Dashboard PRO")),
        "verbouwing":      verbouwing,
        "inboedel":        _load_inboedel(sheets.get("Inboedel begroting")),
        "maand":           _load_maand(sheets.get("Maandelijkse begroting")),
        "budget_verdeling": _load_budget(sheets.get("Budget Verdeling"), rooms, verbouwing),
        "taken":           taken,
        "kosten":          kosten,
        "wensen":          wensen,
        "bonnen":          _load_bonnen(sheets.get("Bonnen")),
        "rooms":           rooms,
    }


def _empty_state() -> dict:
    return {
        "dashboard":       {"Totaal Inleg Patrick": 25000, "Totaal Inleg Willianne": 25000},
        "verbouwing":      pd.DataFrame(columns=VERB_COLS),
        "inboedel":        pd.DataFrame(columns=INBOEDEL_COLS),
        "maand":           [],
        "budget_verdeling": pd.DataFrame(columns=BUDGET_COLS),
        "taken":           {r: [] for r in DEFAULT_ROOMS},
        "kosten":          {r: [] for r in DEFAULT_ROOMS},
        "wensen":          {r: [] for r in DEFAULT_ROOMS},
        "bonnen":          [],
        "rooms":           DEFAULT_ROOMS,
    }


# ── Saver ──────────────────────────────────────────────────────────────────

def _write_sheet(wb, name: str, df: pd.DataFrame) -> None:
    """Verwijder bestaande sheet en schrijf DataFrame opnieuw."""
    if name in wb.sheetnames:
        wb.remove(wb[name])
    ws = wb.create_sheet(name)
    for row in dataframe_to_rows(df, index=False, header=True):
        ws.append(row)


def _room_dict_to_df(room_dict: dict, cols: list) -> pd.DataFrame:
    rows = []
    for kamer, items in room_dict.items():
        for item in items:
            row = {"Kamer": kamer}
            row.update({c: item.get(c, "") for c in cols if c != "Kamer"})
            rows.append(row)
    return pd.DataFrame(rows, columns=cols) if rows else pd.DataFrame(columns=cols)


def save_all_data(state: dict) -> bool:
    """Schrijf de volledige session_state terug naar Excel."""
    if not file_exists():
        st.error("Excel bestand niet gevonden; kan niet opslaan.")
        return False
    try:
        wb = openpyxl.load_workbook(EXCEL_FILE)

        # Dashboard
        dash_df = pd.DataFrame(list(state.get("dashboard", {}).items()), columns=["Sleutel", "Waarde"])
        _write_sheet(wb, "Dashboard PRO", dash_df)

        # Verbouwing
        verb = state.get("verbouwing", pd.DataFrame(columns=VERB_COLS))
        if not isinstance(verb, pd.DataFrame):
            verb = pd.DataFrame(columns=VERB_COLS)
        _write_sheet(wb, "Verbouwing begroting", verb)

        # Inboedel
        inb = state.get("inboedel", pd.DataFrame(columns=INBOEDEL_COLS))
        if not isinstance(inb, pd.DataFrame):
            inb = pd.DataFrame(columns=INBOEDEL_COLS)
        _write_sheet(wb, "Inboedel begroting", inb)

        # Maandelijkse begroting
        maand = state.get("maand", [])
        maand_df = pd.DataFrame(maand, columns=MAAND_COLS) if maand else pd.DataFrame(columns=MAAND_COLS)
        _write_sheet(wb, "Maandelijkse begroting", maand_df)

        # Budget
        bud = state.get("budget_verdeling", pd.DataFrame(columns=BUDGET_COLS))
        _write_sheet(wb, "Budget Verdeling", bud)

        # Kamergerelateerde lijsten
        _write_sheet(wb, "Taken",  _room_dict_to_df(state.get("taken",  {}), TAKEN_COLS))
        _write_sheet(wb, "Kosten", _room_dict_to_df(state.get("kosten", {}), KOSTEN_COLS))
        _write_sheet(wb, "Wensen", _room_dict_to_df(state.get("wensen", {}), WENSEN_COLS))

        # Bonnen
        bonnen = state.get("bonnen", [])
        bonnen_df = pd.DataFrame(bonnen, columns=BONNEN_COLS) if bonnen else pd.DataFrame(columns=BONNEN_COLS)
        _write_sheet(wb, "Bonnen", bonnen_df)

        wb.save(EXCEL_FILE)
        return True
    except Exception as exc:
        st.error(f"Kon Excel niet opslaan: {exc}")
        return False


# ── Specific Save Functions ────────────────────────────────────────────────

def save_verbouwing(df: pd.DataFrame) -> bool:
    """Save verbouwing dataframe to Excel."""
    if not file_exists():
        st.error("Excel bestand niet gevonden.")
        return False
    try:
        wb = openpyxl.load_workbook(EXCEL_FILE)
        _write_sheet(wb, "Verbouwing begroting", df)
        wb.save(EXCEL_FILE)
        return True
    except Exception as exc:
        st.error(f"Kon verbouwing niet opslaan: {exc}")
        return False


def save_inboedel(df: pd.DataFrame) -> bool:
    """Save inboedel dataframe to Excel."""
    if not file_exists():
        st.error("Excel bestand niet gevonden.")
        return False
    try:
        wb = openpyxl.load_workbook(EXCEL_FILE)
        _write_sheet(wb, "Inboedel begroting", df)
        wb.save(EXCEL_FILE)
        return True
    except Exception as exc:
        st.error(f"Kon inboedel niet opslaan: {exc}")
        return False


def save_maand(data: list) -> bool:
    """Save maandelijkse begroting to Excel."""
    if not file_exists():
        st.error("Excel bestand niet gevonden.")
        return False
    try:
        wb = openpyxl.load_workbook(EXCEL_FILE)
        df = pd.DataFrame(data) if data else pd.DataFrame()
        _write_sheet(wb, "Maandelijkse begroting", df)
        wb.save(EXCEL_FILE)
        return True
    except Exception as exc:
        st.error(f"Kon maandelijkse begroting niet opslaan: {exc}")
        return False


def save_dashboard(data: dict) -> bool:
    """Save dashboard dict to Excel."""
    if not file_exists():
        st.error("Excel bestand niet gevonden.")
        return False
    try:
        wb = openpyxl.load_workbook(EXCEL_FILE)
        df = pd.DataFrame(list(data.items()), columns=["Sleutel", "Waarde"])
        _write_sheet(wb, "Dashboard PRO", df)
        wb.save(EXCEL_FILE)
        return True
    except Exception as exc:
        st.error(f"Kon dashboard niet opslaan: {exc}")
        return False
