"""
utils/state.py  –  Hofakkers 44  v3.0

NIEUW v3:
- Buffer-DataFrame in session_state met Begroot_Override (€)
- transfer_envelope(): YNAB drag-and-drop logic tussen envelopes/buffer
- get_effective_budget(): begroting met overrides toegepast
- Fix _v3_loaded flag (i.p.v. _v2_loaded zodat init() correct herlaadt na save)
"""
import streamlit as st
import pandas as pd
from utils.excel_handler import (
    load_all_data, save_buffer,
    KOSTEN_COLS, BUFFER_COLS, VERB_COLS,
)
from utils.config import YNAB_WARN_PCT, YNAB_CRIT_PCT


# ── Initialisatie ──────────────────────────────────────────────────────────

def init() -> None:
    """
    Laad data; herlaadt automatisch als invalidate_cache() de flag heeft gereset.
    Roept ook init_planning() aan zodat planning altijd correct is na (her)laden.
    """
    if st.session_state.get("_v3_loaded"):
        return
    data = load_all_data()
    for k, v in data.items():
        st.session_state[k] = v
    st.session_state["_v3_loaded"] = True
    # Initialiseer planning: laadt uit Excel als beschikbaar, anders defaults
    from utils.planning import init_planning
    init_planning()


def reload() -> None:
    """
    Herlaad alle data uit Excel.
    Reset zowel de data-flag als de planning zodat
    load_all_data() vers uit Excel laadt — ook de Planning-sheet.
    """
    st.session_state["_v3_loaded"] = False
    st.session_state.pop("planning", None)
    init()


# ── Excel opslaan ──────────────────────────────────────────────────────────

def save_all_to_excel() -> bool:
    """
    Schrijf de volledige session_state atomisch naar Excel.
    Enkelvoudig toegangspunt voor sidebar en alle pagina's.
    """
    from utils.excel_handler import save_all_data
    return save_all_data({
        "dashboard":  st.session_state.get("dashboard",  {}),
        "verbouwing": st.session_state.get("verbouwing", pd.DataFrame()),
        "inboedel":   st.session_state.get("inboedel",   pd.DataFrame()),
        "maand":      st.session_state.get("maand",      []),
        "kosten":     st.session_state.get("kosten",     pd.DataFrame()),
        "buffer":     st.session_state.get("buffer",     pd.DataFrame()),
        "planning":   st.session_state.get("planning",   []),
    })


# ── Getters / setters ──────────────────────────────────────────────────────

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


def get_kosten_df() -> pd.DataFrame:
    k = st.session_state.get("kosten", pd.DataFrame())
    if not isinstance(k, pd.DataFrame):
        return pd.DataFrame(columns=KOSTEN_COLS)
    return k


def get_buffer_df() -> pd.DataFrame:
    """Buffer-overrides DataFrame."""
    b = st.session_state.get("buffer", pd.DataFrame())
    if not isinstance(b, pd.DataFrame):
        return pd.DataFrame(columns=BUFFER_COLS)
    if b.empty:
        return pd.DataFrame(columns=BUFFER_COLS)
    return b


def set_dashboard(data: dict) -> None:
    st.session_state["dashboard"] = data


def set_verbouwing(df: pd.DataFrame) -> None:
    st.session_state["verbouwing"] = df.copy()


def set_inboedel(df: pd.DataFrame) -> None:
    st.session_state["inboedel"] = df.copy()


def set_maand(rows: list) -> None:
    st.session_state["maand"] = rows


def set_kosten_df(df: pd.DataFrame) -> None:
    st.session_state["kosten"] = df.copy()


def set_buffer_df(df: pd.DataFrame) -> None:
    st.session_state["buffer"] = df.copy()


# ── Helper ─────────────────────────────────────────────────────────────────

def _sf(v) -> float:
    try:
        return float(str(v or 0).replace(",",".").replace("€","").strip())
    except (TypeError, ValueError):
        return 0.0


# ── Effectieve budgetten (Begroting + Override) ───────────────────────────

def _apply_overrides(cats: dict[str, float], type_: str) -> dict[str, float]:
    """Pas Buffer-overrides toe op een categorie-dict."""
    buf = get_buffer_df()
    if buf.empty:
        return cats.copy()
    result = cats.copy()
    for _, row in buf.iterrows():
        cat = str(row.get("Categorie","")).strip()
        rt  = str(row.get("Type","")).strip().lower()
        if rt != type_.lower() or not cat:
            continue
        override = _sf(row.get("Begroot_Override (€)"))
        if cat in result:
            result[cat] = max(result[cat] + override, 0.0)
        else:
            # Override voor een nieuwe categorie (zelden, maar mogelijk)
            if override > 0:
                result[cat] = override
    return result


def _verb_totals_raw() -> dict[str, float]:
    df = verbouwing()
    if df.empty or "Categorie" not in df.columns:
        return {}
    df = df.copy()
    df["Totaal (€)"] = pd.to_numeric(df["Totaal (€)"], errors="coerce").fillna(0)
    return (df.groupby("Categorie")["Totaal (€)"].sum()
              .where(lambda x: x > 0).dropna().to_dict())


def _inbo_totals_raw() -> dict[str, float]:
    df = inboedel()
    if df.empty or "Categorie" not in df.columns:
        return {}
    df = df.copy()
    df["Totaal (€)"] = pd.to_numeric(df["Totaal (€)"], errors="coerce").fillna(0)
    return (df.groupby("Categorie")["Totaal (€)"].sum()
              .where(lambda x: x > 0).dropna().to_dict())


def _verb_totals() -> dict[str, float]:
    """Verbouwing totalen MET overrides toegepast."""
    return _apply_overrides(_verb_totals_raw(), "verbouwing")


def _inbo_totals() -> dict[str, float]:
    """Inboedel totalen MET overrides toegepast."""
    return _apply_overrides(_inbo_totals_raw(), "inboedel")


# ── Basis berekeningen ─────────────────────────────────────────────────────

def calc_verbouwing_totalen() -> dict:
    cats = _verb_totals()
    return {"categorieën": cats, "totaal": sum(cats.values())}


def calc_inboedel_totalen() -> dict:
    cats = _inbo_totals()
    return {"categorieën": cats, "totaal": sum(cats.values())}


def calc_maand_totalen() -> dict:
    d = dash()
    inkomen  = _sf(d.get("Netto inkomen per maand"))
    vaste    = _sf(d.get("Vaste lasten per maand (wonen + verzekeringen + vervoer)"))
    variabel = _sf(d.get("Variabele lasten per maand (boodschappen + vrijetijd)"))
    spar     = _sf(d.get("Sparen & beleggen per maand"))
    if inkomen == 0:
        for row in maand():
            cat    = str(row.get("Categorie","")).upper()
            bedrag = _sf(row.get("Bedrag (€)") or row.get("bedrag"))
            if "INKOMST" in cat:    inkomen  += bedrag
            elif cat in ("WONEN","VERZEKERING","VERVOER","VASTE"): vaste += bedrag
            elif cat in ("BOODSCHAP","VARIABEL","PERSOONLIJK","VRIJETIJD"): variabel += bedrag
            elif "SPAR" in cat or "BELEGG" in cat: spar += bedrag
    totuit = vaste + variabel + spar
    return {"inkomen": inkomen, "vaste": vaste, "variabel": variabel,
            "sparen": spar, "ruimte": inkomen - totuit, "totaal_uitgaven": totuit}


def calc_project() -> dict:
    d        = dash()
    verb_sum = sum(_verb_totals().values())
    inbo_sum = sum(_inbo_totals().values())
    # Met overrides toegepast → gebruik de berekende som, niet de Dashboard-waarde
    project  = verb_sum + inbo_sum
    return {
        "verbouwing":  verb_sum,
        "inboedel":    inbo_sum,
        "project":     project,
        "per_persoon": project / 2 if project else 0,
        "samen":       _sf(d.get("Samen vermogen na verbouwing")),
        "patrick":     _sf(d.get("Vermogen Patrick na verbouwing")),
        "willianne":   _sf(d.get("Vermogen Willianne na verbouwing")),
    }


def calc_spaargeld() -> dict:
    d = dash()
    pat = _sf(d.get("Vermogen Patrick na verbouwing"))
    wil = _sf(d.get("Vermogen Willianne na verbouwing"))
    return {
        "patrick":       pat,
        "willianne":     wil,
        "samen":         _sf(d.get("Samen vermogen na verbouwing")) or pat + wil,
        "totaal_sparen": _sf(d.get("Totaal sparen + beleggen nu")),
    }


# ── YNAB Engine met Override-support ──────────────────────────────────────

def calc_ynab_envelopes() -> dict:
    """
    Retourneert YNAB envelope-state met Begroot inclusief overrides.
    """
    d            = dash()
    totaal_now   = _sf(d.get("Totaal sparen + beleggen nu"))
    verm         = calc_spaargeld()
    totaal_inleg = totaal_now or (verm["patrick"] + verm["willianne"] +
                                   _sf(d.get("Projectkosten samen (verbouwing + inboedel)")))

    verb_cats = _verb_totals()  # met overrides
    inbo_cats = _inbo_totals()  # met overrides

    kosten_df = get_kosten_df()
    real_per_cat: dict[str, float] = {}
    if not kosten_df.empty and "Categorie" in kosten_df.columns and "Bedrag (€)" in kosten_df.columns:
        kosten_df = kosten_df.copy()
        kosten_df["Bedrag (€)"] = pd.to_numeric(kosten_df["Bedrag (€)"], errors="coerce").fillna(0)
        real_per_cat = kosten_df.groupby("Categorie")["Bedrag (€)"].sum().to_dict()

    def _env(naam, type_, begroot):
        real  = real_per_cat.get(naam, 0.0)
        avail = begroot - real
        pct   = real / begroot * 100 if begroot > 0 else 0
        status = "over" if pct >= YNAB_CRIT_PCT else "warn" if pct >= YNAB_WARN_PCT else "ok"
        # Detecteer of er een override is
        buf = get_buffer_df()
        override = 0.0
        if not buf.empty:
            mask = (buf["Categorie"] == naam) & \
                   (buf["Type"].astype(str).str.lower() == type_.lower())
            if mask.any():
                override = _sf(buf.loc[mask, "Begroot_Override (€)"].iloc[0])
        return {"naam": naam, "type": type_, "begroot": begroot,
                "gerealiseerd": real, "beschikbaar": avail,
                "pct": pct, "status": status, "override": override}

    envelopes = []
    for naam, b in sorted(verb_cats.items(), key=lambda x: -x[1]):
        envelopes.append(_env(naam, "verbouwing", b))
    for naam, b in sorted(inbo_cats.items(), key=lambda x: -x[1]):
        envelopes.append(_env(naam, "inboedel", b))

    toegewezen = sum(e["begroot"] for e in envelopes)
    vrij       = totaal_inleg - toegewezen

    return {
        "totaal_inleg": totaal_inleg,
        "toegewezen":   toegewezen,
        "vrij":         vrij,
        "envelopes":    envelopes,
    }


# ── YNAB Transfer logic ────────────────────────────────────────────────────

def transfer_envelope(
    bron: str,            # "buffer" of categorie-naam
    bron_type: str,       # "" (voor buffer) of "verbouwing" / "inboedel"
    doel: str,            # categorie-naam
    doel_type: str,       # "verbouwing" / "inboedel"
    bedrag: float,
    notitie: str = "",
) -> tuple[bool, str]:
    """
    Verschuif geld tussen envelopes (of vanuit/naar buffer).
    Werkt door overrides toe te voegen aan de Buffer-sheet.

    Returns: (success, message)
    """
    if bedrag <= 0:
        return False, "Bedrag moet positief zijn."

    if bron == doel and bron_type == doel_type:
        return False, "Bron en doel mogen niet identiek zijn."

    # ── Backend validatie: niet meer overdragen dan beschikbaar ──
    ynab = calc_ynab_envelopes()
    if bron == "buffer":
        if bedrag > ynab["vrij"] + 0.01:
            return False, f"❌ Onvoldoende vrije buffer (€ {ynab['vrij']:,.2f} beschikbaar)."
    else:
        bron_env = next((e for e in ynab["envelopes"]
                          if e["naam"] == bron and e["type"] == bron_type), None)
        if not bron_env:
            return False, f"❌ Bron-envelope '{bron}' niet gevonden."
        if bedrag > bron_env["begroot"] + 0.01:
            return False, f"❌ Onvoldoende budget in '{bron}' (€ {bron_env['begroot']:,.2f} beschikbaar)."

    buf_df = get_buffer_df().copy()
    if buf_df.empty:
        buf_df = pd.DataFrame(columns=BUFFER_COLS)

    timestamp = pd.Timestamp.now().strftime("%Y-%m-%d %H:%M")

    # ── Bron is BUFFER ──
    if bron == "buffer":
        # Trek bedrag uit buffer = voeg + bedrag override toe aan doel
        # (Begrote omhoog → buffer slinkt automatisch)
        _add_or_update_override(buf_df, doel, doel_type, +bedrag,
                                f"[{timestamp}] Toegewezen vanuit buffer. {notitie}")

    # ── Doel is BUFFER ──
    elif doel == "buffer":
        # Bron-budget verlagen → buffer groeit automatisch
        _add_or_update_override(buf_df, bron, bron_type, -bedrag,
                                f"[{timestamp}] Teruggegeven aan buffer. {notitie}")

    # ── Tussen twee envelopes ──
    else:
        # Bron verlagen + Doel verhogen
        _add_or_update_override(buf_df, bron, bron_type, -bedrag,
                                f"[{timestamp}] → {doel}. {notitie}")
        _add_or_update_override(buf_df, doel, doel_type, +bedrag,
                                f"[{timestamp}] ← {bron}. {notitie}")

    set_buffer_df(buf_df)

    # Direct opslaan naar Excel
    if save_buffer(buf_df):
        # Cache invalideren zodat alle pagina's verse data zien
        return True, f"✅ € {bedrag:,.0f} verschoven."
    else:
        return False, "❌ Opslaan naar Excel mislukt."


def _add_or_update_override(buf_df: pd.DataFrame, cat: str, type_: str,
                             delta: float, notitie: str) -> None:
    """Voeg een override toe of update een bestaande."""
    mask = (buf_df["Categorie"] == cat) & \
           (buf_df["Type"].astype(str).str.lower() == type_.lower())
    if mask.any():
        idx = buf_df.index[mask][0]
        cur = _sf(buf_df.at[idx, "Begroot_Override (€)"])
        buf_df.at[idx, "Begroot_Override (€)"] = cur + delta
        existing_note = str(buf_df.at[idx, "Notitie"] or "")
        buf_df.at[idx, "Notitie"] = (existing_note + " | " + notitie).strip(" |")
    else:
        new_row = pd.DataFrame([{
            "Categorie": cat,
            "Type": type_,
            "Begroot_Override (€)": delta,
            "Notitie": notitie,
        }])
        # Append in-place via session_state
        if buf_df.empty:
            buf_df.loc[0] = new_row.iloc[0]
        else:
            buf_df.loc[len(buf_df)] = new_row.iloc[0]


def reset_envelope_overrides() -> bool:
    """Wis alle YNAB-overrides. Reset alle envelopes naar de Excel-begroting."""
    empty = pd.DataFrame(columns=BUFFER_COLS)
    set_buffer_df(empty)
    return save_buffer(empty)


# ── HomeZada Budget vs Actuals ─────────────────────────────────────────────

def calc_budget_vs_actuals() -> pd.DataFrame:
    verb_cats = _verb_totals()
    inbo_cats = _inbo_totals()
    kosten_df = get_kosten_df()
    real_per_cat: dict[str, float] = {}
    if not kosten_df.empty and "Categorie" in kosten_df.columns:
        kosten_df = kosten_df.copy()
        kosten_df["Bedrag (€)"] = pd.to_numeric(kosten_df["Bedrag (€)"], errors="coerce").fillna(0)
        real_per_cat = kosten_df.groupby("Categorie")["Bedrag (€)"].sum().to_dict()

    rows = []
    for naam, begroot in {**verb_cats, **inbo_cats}.items():
        type_ = "Verbouwing" if naam in verb_cats else "Inboedel"
        real  = real_per_cat.get(naam, 0.0)
        diff  = begroot - real
        pct   = real / begroot * 100 if begroot > 0 else 0
        status = "🔴 Over budget" if pct > 100 else \
                 "🟡 Let op"     if pct > 80  else "🟢 On track"
        rows.append({
            "Categorie":         naam,
            "Type":              type_,
            "Begroot (€)":       begroot,
            "Gerealiseerd (€)":  real,
            "Verschil (€)":      diff,
            "% Gebruikt":        round(pct, 1),
            "Status":            status,
        })
    return pd.DataFrame(rows) if rows else pd.DataFrame(
        columns=["Categorie","Type","Begroot (€)","Gerealiseerd (€)",
                 "Verschil (€)","% Gebruikt","Status"])


def calc_room_status_smart(begroot: float, gerealiseerd: float, n_posten: int) -> str:
    """
    Slimmere statusbepaling dan v2:
    - 0 posten             → Planningsfase
    - 0% gerealiseerd      → Planningsfase
    - 0–99% gerealiseerd   → In uitvoering
    - >= 100% gerealiseerd → Klaar
    """
    if n_posten == 0:
        return "Planningsfase"
    if begroot == 0 or gerealiseerd == 0:
        return "Planningsfase"
    pct = gerealiseerd / begroot * 100
    if pct >= 100:
        return "Klaar"
    return "In uitvoering"
