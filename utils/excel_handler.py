"""
utils/excel_handler.py  –  Hofakkers 44
Robuuste Excel I/O – laadt alle 7 sheets exact zoals ze in de echte Excel staan.

BUGS FIXED:
- _load_inboedel: re-reads with header=1 (was using wrong header, gave empty DataFrame)
- _load_maand: uses correct sheet name "Maandbegroting" and correct column parser
- Added _load_sparen() and _load_hypotheek()
- save_all_data() correctly required state dict
"""
import streamlit as st
import pandas as pd
import openpyxl
from openpyxl.utils.dataframe import dataframe_to_rows
from pathlib import Path

from utils.config import (
    EXCEL_FILE, DEFAULT_ROOMS,
    SH_DASHBOARD, SH_MAAND, SH_VERBOUWING, SH_INBOEDEL,
    SH_SPAREN, SH_HYPOTHEEK,
)

# ── Kolom definities ───────────────────────────────────────────────────────
VERB_COLS    = ["Categorie", "Post", "Aantal", "Eenheid",
                "Kosten per eenheid (€)", "Totaal (€)", "Opmerking"]
INBOEDEL_COLS = ["Categorie", "Post", "Aantal", "Eenheid",
                 "Kosten per eenheid (€)", "Totaal (€)", "Opmerking"]
MAAND_COLS   = ["Categorie", "Post", "Bedrag (€)"]
TAKEN_COLS   = ["Kamer", "Taak", "Status", "Verantwoordelijke", "Deadline", "Opmerking"]
KOSTEN_COLS  = ["Kamer", "Datum", "Leverancier", "Bedrag (€)", "Categorie", "Omschrijving"]
WENSEN_COLS  = ["Kamer", "Wens", "Status", "Prioriteit", "Geschat Bedrag (€)", "Opmerking"]
BONNEN_COLS  = ["Datum", "Leverancier", "Bedrag (€)", "Categorie", "Kamer", "Omschrijving", "BTW (€)"]
BUDGET_COLS  = ["Kamer", "Toegewezen Budget (€)", "Gerealiseerd (€)", "Beschikbaar (€)"]


def file_exists() -> bool:
    return EXCEL_FILE.exists()


def _sf(v) -> float:
    try:
        return float(v or 0)
    except (TypeError, ValueError):
        return 0.0


def _safe_read_excel() -> dict:
    """Laad alle sheets als {naam: DataFrame} met header=0."""
    try:
        return pd.read_excel(EXCEL_FILE, sheet_name=None, engine="openpyxl")
    except Exception as exc:
        raise RuntimeError(f"Kon Excel niet lezen: {exc}") from exc


def _norm_cols(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df.columns = [str(c).strip() for c in df.columns]
    return df


def _ensure_cols(df: pd.DataFrame, cols: list, defaults: dict = None) -> pd.DataFrame:
    defaults = defaults or {}
    for c in cols:
        if c not in df.columns:
            df[c] = defaults.get(c, "")
    return df[cols].copy()


# ── Dashboard PRO ──────────────────────────────────────────────────────────

def _load_dashboard(df: pd.DataFrame) -> dict:
    """
    Sheet: col A = label, col B = waarde (geen header row).
    Gelezen met header=0 → rij 0 wordt kolomnaam, data begint rij 1.
    Itereert op iloc positie dus werkt correct.
    """
    if df is None or df.empty:
        return {}
    result = {}
    for _, row in df.iterrows():
        key = str(row.iloc[0]).strip() if pd.notna(row.iloc[0]) else ""
        if not key or key.lower() in ("nan", "none", ""):
            continue
        val = row.iloc[1] if len(row) > 1 and pd.notna(row.iloc[1]) else None
        if val is not None:
            result[key] = val
    return result


# ── Verbouwing begroting ───────────────────────────────────────────────────

def _map_section_to_cat(section: str) -> str:
    """Gebruik de sectienaam direct als categorie (cleanups only)."""
    if not isinstance(section, str):
        return "Overig"
    s = section.strip()
    return s if s else "Overig"


def _parse_begroting_sheet(df: pd.DataFrame, sheet_name: str) -> pd.DataFrame:
    """
    Generieke parser voor Verbouwing- en Inboedel-sheets.
    Structuur: rij 0 = titel, rij 1 = headers (Categorie, Post, Aantal, ...)
    Gelezen met header=0: kolomnamen zijn de titeltekst.
    Fix: re-read met header=1 om echte headers te pakken.
    """
    try:
        df = pd.read_excel(EXCEL_FILE, sheet_name=sheet_name, header=1, engine="openpyxl")
    except Exception:
        return pd.DataFrame(columns=VERB_COLS)

    df = _norm_cols(df)

    # Zorg dat alle vereiste kolommen bestaan
    for col in VERB_COLS:
        if col not in df.columns:
            df[col] = "" if col in ("Categorie", "Post", "Eenheid", "Opmerking") else 0.0

    current_section = "Overig"
    rows = []

    for _, row in df.iterrows():
        cat_raw  = row["Categorie"]
        post_raw = row["Post"]
        aantal   = row["Aantal"]
        eenheid  = row["Eenheid"]
        kosten_p = row["Kosten per eenheid (€)"]
        totaal   = row["Totaal (€)"]
        opmerking = row["Opmerking"]

        post_str = str(post_raw).strip() if pd.notna(post_raw) else ""
        cat_str  = str(cat_raw).strip()  if pd.notna(cat_raw)  else ""

        # Sla totaalrijen over (Post begint met 'Totaal' of 'toaal')
        if post_str.lower().startswith("totaal") or post_str.lower().startswith("toaal"):
            continue

        # Sectie-header: categorie gevuld, post leeg, geen numeriek in kosten
        if cat_str and not post_str:
            if not cat_str.lower().startswith("totale"):
                current_section = cat_str
            continue

        # Sla lege Post-rijen over
        if not post_str or post_str.lower() == "nan":
            continue

        # Sla de titeltabelrij over (Categorie = 'Totale verwachting kosten')
        if cat_str.lower().startswith("totale"):
            continue

        n   = _sf(aantal)
        kpu = _sf(kosten_p)
        tot = _sf(totaal) or (n * kpu)

        rows.append({
            "Categorie":              cat_str if cat_str and cat_str.lower() != "nan" else current_section,
            "Post":                   post_str,
            "Aantal":                 n,
            "Eenheid":                str(eenheid).strip() if pd.notna(eenheid) else "",
            "Kosten per eenheid (€)": kpu,
            "Totaal (€)":             tot,
            "Opmerking":              str(opmerking).strip() if pd.notna(opmerking) else "",
        })

    if not rows:
        return pd.DataFrame(columns=VERB_COLS)
    return pd.DataFrame(rows, columns=VERB_COLS).reset_index(drop=True)


# ── Maandbegroting ─────────────────────────────────────────────────────────

def _load_maand(sheets: dict) -> list:
    """
    Parse Maandbegroting sheet naar [{categorie, post, bedrag}].
    Sheet heeft geen vaste tabel-structuur; labels staan in col A/B, bedragen in col D.
    BUG FIX: correct sheet name + correct column index (3) voor bedrag.
    """
    df = sheets.get(SH_MAAND)  # "Maandbegroting"
    if df is None or df.empty:
        return []

    rows = []
    huidig_cat = "Algemeen"

    for _, row in df.iterrows():
        col0 = str(row.iloc[0]).strip() if pd.notna(row.iloc[0]) else ""
        col1 = str(row.iloc[1]).strip() if len(row) > 1 and pd.notna(row.iloc[1]) else ""

        # Bedrag staat in kolom D (index 3)
        bedrag_raw = row.iloc[3] if len(row) > 3 else None
        try:
            bedrag = float(bedrag_raw)
        except (TypeError, ValueError):
            bedrag = None

        # Detecteer categorie-headers (tekst in col A, geen bedrag in col D)
        if col0 and col0 not in ("nan", "None") and bedrag is None:
            skip = ("INKOMSTEN & TOESLAGEN", "VARIABELE LASTEN & SPAREN",
                    "OVERZICHT", "nan")
            if col0 not in skip:
                huidig_cat = col0
            continue

        # Rijen met bedrag > 0
        if bedrag is not None and bedrag > 0:
            post = col1 if col1 and col1 not in ("nan", "None") else col0
            if post and post.lower() not in ("nan", "none", ""):
                rows.append({
                    "Categorie": huidig_cat,
                    "Post":      post,
                    "Bedrag (€)": bedrag,
                })
    return rows


# ── Sparen & Beleggen ──────────────────────────────────────────────────────

def _load_sparen(sheets: dict) -> dict:
    """Laad spaarparameters en projectietabel."""
    df = sheets.get(SH_SPAREN)
    if df is None or df.empty:
        return {"startwaarde": 0, "maandinleg": 500, "rendement": 0.05, "periode": 30, "tabel": pd.DataFrame()}

    params = {}
    tabel_rows = []
    for _, row in df.iterrows():
        k = str(row.iloc[0]).strip() if pd.notna(row.iloc[0]) else ""
        v = row.iloc[1] if len(row) > 1 and pd.notna(row.iloc[1]) else None

        if "startwaarde" in k.lower():
            params["startwaarde"] = _sf(v)
        elif "maandelijkse inleg" in k.lower():
            params["maandinleg"] = _sf(v)
        elif "verwacht" in k.lower() and "rendement" in k.lower():
            params["rendement"] = _sf(v)
        elif "periode" in k.lower():
            params["periode"] = int(_sf(v))

        # Jaarprojectietabel: kolom A = jaarnummer (1-50)
        try:
            jaar = int(row.iloc[0])
            if 1 <= jaar <= 50 and len(row) >= 5:
                tabel_rows.append({
                    "Jaar":           jaar,
                    "Beginwaarde (€)": _sf(row.iloc[1]),
                    "Inleg (€)":       _sf(row.iloc[2]),
                    "Rendement (€)":   _sf(row.iloc[3]),
                    "Eindwaarde (€)":  _sf(row.iloc[4]),
                })
        except (TypeError, ValueError):
            pass

    params.setdefault("startwaarde", 0)
    params.setdefault("maandinleg",  500)
    params.setdefault("rendement",   0.05)
    params.setdefault("periode",     30)
    params["tabel"] = pd.DataFrame(tabel_rows) if tabel_rows else pd.DataFrame(
        columns=["Jaar","Beginwaarde (€)","Inleg (€)","Rendement (€)","Eindwaarde (€)"])
    return params


# ── Hypotheek ──────────────────────────────────────────────────────────────

def _load_hypotheek(sheets: dict) -> dict:
    """Laad hypotheekparameters en annuïteitentabel."""
    df = sheets.get(SH_HYPOTHEEK)
    if df is None or df.empty:
        return {"params": {}, "tabel": pd.DataFrame()}

    params = {}
    rows = []
    for _, row in df.iterrows():
        # Parameters staan in kolommen H–I (index 7–8)
        if len(row) > 8 and pd.notna(row.iloc[7]) and pd.notna(row.iloc[8]):
            k = str(row.iloc[7]).strip()
            v = row.iloc[8]
            if k and k.lower() not in ("nan", "none"):
                try:
                    params[k] = float(v)
                except (TypeError, ValueError):
                    params[k] = v

        # Annuïteitentabel: kolom A = maandnummer
        try:
            periode = int(row.iloc[0])
            if 1 <= periode <= 360 and len(row) >= 6:
                rows.append({
                    "Maand":             periode,
                    "Totale schuld (€)": _sf(row.iloc[1]),
                    "Rente (€)":         _sf(row.iloc[2]),
                    "Aflossing (€)":     _sf(row.iloc[3]),
                    "Restschuld (€)":    _sf(row.iloc[4]),
                    "Maandbedrag (€)":   _sf(row.iloc[5]),
                })
        except (TypeError, ValueError):
            pass

    return {
        "params": params,
        "tabel":  pd.DataFrame(rows) if rows else pd.DataFrame(),
    }


# ── Optionele kamers-sheets ────────────────────────────────────────────────

def _load_room_list(df: pd.DataFrame, cols: list) -> dict:
    result: dict = {}
    if df is None or df.empty:
        return result
    df = _norm_cols(df)
    for c in cols:
        if c not in df.columns:
            df[c] = ""
    df = df[cols].copy()
    df["Kamer"] = df["Kamer"].fillna("Algemeen").astype(str).str.strip()
    for _, row in df.iterrows():
        kamer = row["Kamer"]
        item = {c: row[c] for c in cols}
        for k, v in item.items():
            if isinstance(v, float) and pd.isna(v):
                item[k] = ""
        result.setdefault(kamer, []).append(item)
    return result


def _load_bonnen(df: pd.DataFrame) -> list:
    if df is None or df.empty:
        return []
    df = _norm_cols(df)
    for c in BONNEN_COLS:
        if c not in df.columns:
            df[c] = ""
    return df[BONNEN_COLS].to_dict(orient="records")


# ── Hoofd-loader ───────────────────────────────────────────────────────────

def load_all_data() -> dict:
    """
    Laad alle sheets uit de echte Excel.
    Fouttolerant: ontbrekende sheets geven lege defaults.
    """
    if not file_exists():
        return _empty_state()

    try:
        sheets = _safe_read_excel()
    except RuntimeError as exc:
        return _empty_state()

    # Verbouwing en Inboedel via de gespecialiseerde parser (header=1)
    verbouwing = _parse_begroting_sheet(sheets.get(SH_VERBOUWING), SH_VERBOUWING)
    inboedel   = _parse_begroting_sheet(sheets.get(SH_INBOEDEL),   SH_INBOEDEL)

    # Dashboard en maand via raw-parser
    dashboard = _load_dashboard(sheets.get(SH_DASHBOARD))
    maand     = _load_maand(sheets)

    # Optionele sheets
    taken  = _load_room_list(sheets.get("Taken"),  TAKEN_COLS)  if "Taken"  in (sheets or {}) else {}
    kosten = _load_room_list(sheets.get("Kosten"), KOSTEN_COLS) if "Kosten" in (sheets or {}) else {}
    wensen = _load_room_list(sheets.get("Wensen"), WENSEN_COLS) if "Wensen" in (sheets or {}) else {}
    bonnen = _load_bonnen(sheets.get("Bonnen"))                  if "Bonnen" in (sheets or {}) else []

    rooms = DEFAULT_ROOMS[:]
    for kamer in rooms:
        taken.setdefault(kamer, [])
        kosten.setdefault(kamer, [])
        wensen.setdefault(kamer, [])

    return {
        "dashboard":  dashboard,
        "verbouwing": verbouwing,
        "inboedel":   inboedel,
        "maand":      maand,
        "sparen":     _load_sparen(sheets),
        "hypotheek":  _load_hypotheek(sheets),
        "taken":      taken,
        "kosten":     kosten,
        "wensen":     wensen,
        "bonnen":     bonnen,
        "rooms":      rooms,
    }


def _empty_state() -> dict:
    return {
        "dashboard":  {},
        "verbouwing": pd.DataFrame(columns=VERB_COLS),
        "inboedel":   pd.DataFrame(columns=INBOEDEL_COLS),
        "maand":      [],
        "sparen":     {"startwaarde": 0, "maandinleg": 500, "rendement": 0.05, "periode": 30,
                       "tabel": pd.DataFrame()},
        "hypotheek":  {"params": {}, "tabel": pd.DataFrame()},
        "taken":      {r: [] for r in DEFAULT_ROOMS},
        "kosten":     {r: [] for r in DEFAULT_ROOMS},
        "wensen":     {r: [] for r in DEFAULT_ROOMS},
        "bonnen":     [],
        "rooms":      DEFAULT_ROOMS[:],
    }


# ── Saver helpers ──────────────────────────────────────────────────────────

def _write_sheet(wb, name: str, df: pd.DataFrame) -> None:
    if name in wb.sheetnames:
        wb.remove(wb[name])
    ws = wb.create_sheet(name)
    for row in dataframe_to_rows(df, index=False, header=True):
        ws.append(row)


def _room_dict_to_df(room_dict: dict, cols: list) -> pd.DataFrame:
    rows = []
    for kamer, items in room_dict.items():
        for item in items:
            row = {c: item.get(c, "") for c in cols}
            row["Kamer"] = kamer
            rows.append(row)
    return pd.DataFrame(rows, columns=cols) if rows else pd.DataFrame(columns=cols)


# ── Specifieke savers ──────────────────────────────────────────────────────

def save_verbouwing(df: pd.DataFrame) -> bool:
    if not file_exists():
        return False
    try:
        wb = openpyxl.load_workbook(EXCEL_FILE)
        _write_sheet(wb, SH_VERBOUWING, df)
        wb.save(EXCEL_FILE)
        return True
    except Exception:
        return False


def save_inboedel(df: pd.DataFrame) -> bool:
    if not file_exists():
        return False
    try:
        wb = openpyxl.load_workbook(EXCEL_FILE)
        _write_sheet(wb, SH_INBOEDEL, df)
        wb.save(EXCEL_FILE)
        return True
    except Exception:
        return False


def save_dashboard(data: dict) -> bool:
    if not file_exists():
        return False
    try:
        wb = openpyxl.load_workbook(EXCEL_FILE)
        df = pd.DataFrame(list(data.items()), columns=["Sleutel", "Waarde"])
        _write_sheet(wb, SH_DASHBOARD, df)
        wb.save(EXCEL_FILE)
        return True
    except Exception:
        return False


def save_maand(rows: list) -> bool:
    if not file_exists():
        return False
    try:
        wb = openpyxl.load_workbook(EXCEL_FILE)
        df = pd.DataFrame(rows) if rows else pd.DataFrame(columns=MAAND_COLS)
        _write_sheet(wb, SH_MAAND, df)
        wb.save(EXCEL_FILE)
        return True
    except Exception:
        return False


def save_all_data(state: dict) -> bool:
    """Schrijf de volledige session_state terug naar Excel."""
    if not file_exists():
        return False
    try:
        wb = openpyxl.load_workbook(EXCEL_FILE)

        # Dashboard
        dash_df = pd.DataFrame(list(state.get("dashboard", {}).items()),
                               columns=["Sleutel", "Waarde"])
        _write_sheet(wb, SH_DASHBOARD, dash_df)

        # Verbouwing & Inboedel
        for key, sheet in [("verbouwing", SH_VERBOUWING), ("inboedel", SH_INBOEDEL)]:
            df = state.get(key, pd.DataFrame(columns=VERB_COLS))
            if not isinstance(df, pd.DataFrame):
                df = pd.DataFrame(columns=VERB_COLS)
            _write_sheet(wb, sheet, df)

        # Maandbegroting
        maand = state.get("maand", [])
        maand_df = pd.DataFrame(maand) if maand else pd.DataFrame(columns=MAAND_COLS)
        _write_sheet(wb, SH_MAAND, maand_df)

        # Taken, Kosten, Wensen
        _write_sheet(wb, "Taken",  _room_dict_to_df(state.get("taken",  {}), TAKEN_COLS))
        _write_sheet(wb, "Kosten", _room_dict_to_df(state.get("kosten", {}), KOSTEN_COLS))
        _write_sheet(wb, "Wensen", _room_dict_to_df(state.get("wensen", {}), WENSEN_COLS))

        # Bonnen
        bonnen = state.get("bonnen", [])
        bonnen_df = pd.DataFrame(bonnen) if bonnen else pd.DataFrame(columns=BONNEN_COLS)
        _write_sheet(wb, "Bonnen", bonnen_df)

        wb.save(EXCEL_FILE)
        return True
    except Exception as exc:
        return False
