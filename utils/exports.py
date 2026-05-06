"""
utils/exports.py  –  Hofakkers 44  v4.0

Export-engine: PDF, CSV, Excel.
Altijd gebasseerd op de actuele session_state (inclusief YNAB-overrides).
"""
import io
import csv
import zipfile
from datetime import date, datetime

import pandas as pd
import streamlit as st


def _sf(v) -> float:
    try:
        return float(str(v or 0).replace(",",".").replace("€","").strip())
    except (TypeError, ValueError):
        return 0.0


# ── CSV Exports ────────────────────────────────────────────────────────────

def export_verbouwing_csv() -> bytes:
    df = st.session_state.get("verbouwing", pd.DataFrame())
    if df.empty:
        return b"Geen verbouwingsdata"
    return df.to_csv(index=False, encoding="utf-8-sig").encode()


def export_inboedel_csv() -> bytes:
    df = st.session_state.get("inboedel", pd.DataFrame())
    if df.empty:
        return b"Geen inboedeldata"
    return df.to_csv(index=False, encoding="utf-8-sig").encode()


def export_kosten_csv() -> bytes:
    df = st.session_state.get("kosten", pd.DataFrame())
    if isinstance(df, pd.DataFrame) and not df.empty:
        return df.to_csv(index=False, encoding="utf-8-sig").encode()
    return b"Geen kostendata"


def export_planning_csv() -> bytes:
    planning = st.session_state.get("planning", [])
    if not planning:
        return b"Geen planningsdata"
    df = pd.DataFrame(planning)
    return df.to_csv(index=False, encoding="utf-8-sig").encode()


def export_ynab_csv() -> bytes:
    """YNAB envelope-status als CSV."""
    try:
        from utils.state import calc_ynab_envelopes
        ynab = calc_ynab_envelopes()
        rows = []
        for e in ynab["envelopes"]:
            rows.append({
                "Categorie":         e["naam"],
                "Type":              e["type"].title(),
                "Begroot (€)":       e["begroot"],
                "Gerealiseerd (€)":  e["gerealiseerd"],
                "Beschikbaar (€)":   e["beschikbaar"],
                "% Gebruikt":        round(e["pct"], 1),
                "Override (€)":      e["override"],
                "Status":            e["status"],
            })
        rows.append({
            "Categorie":    "VRIJE BUFFER",
            "Type":         "",
            "Begroot (€)":  ynab["vrij"],
            "Gerealiseerd (€)": 0,
            "Beschikbaar (€)":  ynab["vrij"],
            "% Gebruikt":   0,
            "Override (€)": 0,
            "Status":       "buffer",
        })
        df = pd.DataFrame(rows)
        return df.to_csv(index=False, encoding="utf-8-sig").encode()
    except Exception as exc:
        return f"Fout bij genereren YNAB CSV: {exc}".encode()


# ── Excel Export (volledig overzicht) ──────────────────────────────────────

def export_full_excel() -> bytes:
    """
    Exporteer alle data als een nieuw, leesbaar Excel-bestand.
    Bevat: Samenvatting / YNAB / Verbouwing / Inboedel / Kosten / Planning.
    """
    buf = io.BytesIO()
    with pd.ExcelWriter(buf, engine="xlsxwriter") as writer:
        wb  = writer.book
        ts  = datetime.now().strftime("%d-%m-%Y %H:%M")

        # Formatters
        fmt_header = wb.add_format({"bold":True,"bg_color":"#FFD700",
                                     "border":1,"align":"center"})
        fmt_euro   = wb.add_format({"num_format":"€ #,##0","border":1})
        fmt_pct    = wb.add_format({"num_format":"0.0%","border":1})
        fmt_border = wb.add_format({"border":1})
        fmt_title  = wb.add_format({"bold":True,"font_size":14,"font_color":"#1A1A2E"})
        fmt_red    = wb.add_format({"bold":True,"font_color":"#EF4444","border":1,"num_format":"€ #,##0"})
        fmt_grn    = wb.add_format({"bold":True,"font_color":"#10B981","border":1,"num_format":"€ #,##0"})

        # ── 1. SAMENVATTING ──
        ws = wb.add_worksheet("Samenvatting")
        ws.write(0, 0, "Hofakkers 44 — Export Rapport", fmt_title)
        ws.write(1, 0, f"Gegenereerd op: {ts}", wb.add_format({"italic":True,"font_color":"#6B7280"}))

        try:
            from utils.state import calc_project, calc_spaargeld, calc_maand_totalen
            proj = calc_project()
            verm = calc_spaargeld()
            mt   = calc_maand_totalen()

            rows_sum = [
                ("", ""),
                ("── Project Kosten ──", ""),
                ("Verbouwing totaal",  proj["verbouwing"]),
                ("Inboedel totaal",    proj["inboedel"]),
                ("Totaal project",     proj["project"]),
                ("", ""),
                ("── Vermogen ──", ""),
                ("Totaal gespaard nu",      verm["totaal_sparen"]),
                ("Patrick na verbouwing",   verm["patrick"]),
                ("Willianne na verbouwing", verm["willianne"]),
                ("Samen na verbouwing",     verm["samen"]),
                ("", ""),
                ("── Cashflow (maand) ──", ""),
                ("Netto inkomen",           mt["inkomen"]),
                ("Vaste lasten",            mt["vaste"]),
                ("Variabele lasten",        mt["variabel"]),
                ("Sparen & beleggen",       mt["sparen"]),
                ("Vrije buffer",            mt["ruimte"]),
            ]
            for r, (label, val) in enumerate(rows_sum, start=3):
                ws.write(r, 0, label, fmt_border)
                if isinstance(val, (int, float)) and val != 0:
                    fmt = fmt_grn if val >= 0 else fmt_red
                    ws.write(r, 1, val, fmt)
                else:
                    ws.write(r, 1, "", fmt_border)
            ws.set_column(0, 0, 36)
            ws.set_column(1, 1, 16)
        except Exception:
            ws.write(3, 0, "Data niet beschikbaar")

        # ── 2. YNAB ENVELOPES ──
        try:
            from utils.state import calc_ynab_envelopes
            ynab = calc_ynab_envelopes()
            rows_y = []
            for e in ynab["envelopes"]:
                rows_y.append({
                    "Categorie": e["naam"], "Type": e["type"].title(),
                    "Begroot (€)": e["begroot"], "Gerealiseerd (€)": e["gerealiseerd"],
                    "Beschikbaar (€)": e["beschikbaar"],
                    "% Gebruikt": e["pct"] / 100, "Status": e["status"],
                })
            df_y = pd.DataFrame(rows_y)
            df_y.to_excel(writer, sheet_name="YNAB Envelopes", index=False)
            ws_y = writer.sheets["YNAB Envelopes"]
            ws_y.set_column(0, 0, 30); ws_y.set_column(1, 1, 12)
            ws_y.set_column(2, 4, 18); ws_y.set_column(5, 5, 12)
        except Exception:
            pass

        # ── 3. VERBOUWING ──
        verb = st.session_state.get("verbouwing", pd.DataFrame())
        if not verb.empty:
            verb.to_excel(writer, sheet_name="Verbouwing", index=False)
            ws_v = writer.sheets["Verbouwing"]
            ws_v.set_column(0, 0, 28); ws_v.set_column(1, 1, 36)
            ws_v.set_column(2, 6, 14)

        # ── 4. INBOEDEL ──
        inbo = st.session_state.get("inboedel", pd.DataFrame())
        if not inbo.empty:
            inbo.to_excel(writer, sheet_name="Inboedel", index=False)
            ws_i = writer.sheets["Inboedel"]
            ws_i.set_column(0, 0, 28); ws_i.set_column(1, 1, 36)

        # ── 5. KOSTEN ──
        kosten = st.session_state.get("kosten", pd.DataFrame())
        if isinstance(kosten, pd.DataFrame) and not kosten.empty:
            kosten.to_excel(writer, sheet_name="Kosten", index=False)

        # ── 6. PLANNING ──
        planning = st.session_state.get("planning", [])
        if planning:
            df_p = pd.DataFrame(planning)
            df_p.to_excel(writer, sheet_name="Planning", index=False)
            ws_p = writer.sheets["Planning"]
            ws_p.set_column(0, 0, 32); ws_p.set_column(1, 5, 16)

    return buf.getvalue()


# ── ZIP: alles in één download ─────────────────────────────────────────────

def export_all_zip() -> bytes:
    """Bundel alle CSVs + Excel in één ZIP."""
    ts = date.today().strftime("%Y%m%d")
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr(f"hofakkers44_{ts}_verbouwing.csv",  export_verbouwing_csv())
        zf.writestr(f"hofakkers44_{ts}_inboedel.csv",    export_inboedel_csv())
        zf.writestr(f"hofakkers44_{ts}_kosten.csv",      export_kosten_csv())
        zf.writestr(f"hofakkers44_{ts}_planning.csv",    export_planning_csv())
        zf.writestr(f"hofakkers44_{ts}_ynab.csv",        export_ynab_csv())
        zf.writestr(f"hofakkers44_{ts}_volledig.xlsx",   export_full_excel())
    return buf.getvalue()


# ── PDF: YNAB Statusrapport ────────────────────────────────────────────────

def export_ynab_pdf() -> bytes:
    """
    Genereert een simpele PDF van het YNAB overzicht via ReportLab.
    Fallback naar tekst-PDF als ReportLab niet beschikbaar is.
    """
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib import colors
        from reportlab.platypus import (
            SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
        )
        from reportlab.lib.units import cm

        from utils.state import calc_ynab_envelopes, calc_project, calc_spaargeld

        ynab = calc_ynab_envelopes()
        proj = calc_project()
        verm = calc_spaargeld()

        buf = io.BytesIO()
        doc = SimpleDocTemplate(buf, pagesize=A4,
                                rightMargin=2*cm, leftMargin=2*cm,
                                topMargin=2*cm, bottomMargin=2*cm)
        styles = getSampleStyleSheet()
        story  = []

        # Titel
        story.append(Paragraph("<b>Hofakkers 44 – YNAB Budgetrapport</b>",
                                ParagraphStyle("T", fontSize=18, spaceAfter=4,
                                               textColor=colors.HexColor("#1A1A2E"))))
        ts = datetime.now().strftime("%d-%m-%Y %H:%M")
        story.append(Paragraph(f"Gegenereerd: {ts}",
                                ParagraphStyle("S", fontSize=9, textColor=colors.grey)))
        story.append(Spacer(1, 0.5*cm))

        # Samenvatting
        sum_data = [
            ["Totaal Inleg",   f"€ {ynab['totaal_inleg']:,.0f}"],
            ["Toegewezen",     f"€ {ynab['toegewezen']:,.0f}"],
            ["Vrije Buffer",   f"€ {ynab['vrij']:,.0f}"],
            ["Verbouwing",     f"€ {proj['verbouwing']:,.0f}"],
            ["Inboedel",       f"€ {proj['inboedel']:,.0f}"],
            ["Samen resterend",f"€ {verm['samen']:,.0f}"],
        ]
        t_sum = Table(sum_data, colWidths=[7*cm, 5*cm])
        t_sum.setStyle(TableStyle([
            ("BACKGROUND", (0,0), (-1,-1), colors.HexColor("#FFFBEB")),
            ("TEXTCOLOR",  (0,0), (0,-1), colors.HexColor("#6B7280")),
            ("FONTNAME",   (1,0), (1,-1), "Helvetica-Bold"),
            ("GRID",       (0,0), (-1,-1), 0.5, colors.HexColor("#E5E7EB")),
            ("ROWBACKGROUNDS",(0,0),(-1,-1),
             [colors.HexColor("#FFFBEB"), colors.HexColor("#FFFFFF")]),
            ("PADDING",    (0,0),(-1,-1), 6),
        ]))
        story.append(t_sum)
        story.append(Spacer(1, 0.6*cm))

        # Envelopes tabel
        story.append(Paragraph("<b>Envelope Status</b>",
                                ParagraphStyle("H2", fontSize=12, spaceAfter=6,
                                               textColor=colors.HexColor("#1A1A2E"))))

        env_data = [["Categorie", "Type", "Begroot", "Besteed", "Beschikbaar", "%"]]
        for e in ynab["envelopes"]:
            pct_str = f"{e['pct']:.0f}%"
            row = [
                e["naam"], e["type"].title(),
                f"€ {e['begroot']:,.0f}",
                f"€ {e['gerealiseerd']:,.0f}",
                f"€ {e['beschikbaar']:,.0f}",
                pct_str,
            ]
            env_data.append(row)

        t_env = Table(env_data, colWidths=[5.5*cm, 2.5*cm, 3*cm, 3*cm, 3*cm, 1.5*cm])
        env_style = [
            ("BACKGROUND", (0,0), (-1,0), colors.HexColor("#FFD700")),
            ("FONTNAME",   (0,0), (-1,0), "Helvetica-Bold"),
            ("GRID",       (0,0), (-1,-1), 0.5, colors.HexColor("#E5E7EB")),
            ("FONTSIZE",   (0,0), (-1,-1), 8),
            ("PADDING",    (0,0), (-1,-1), 5),
            ("ROWBACKGROUNDS", (0,1), (-1,-1),
             [colors.HexColor("#FFFFFF"), colors.HexColor("#FFFBEB")]),
        ]
        # Kleurtinten voor over-budget rijen
        for i, e in enumerate(ynab["envelopes"], start=1):
            if e["status"] == "over":
                env_style.append(("BACKGROUND",(4,i),(4,i), colors.HexColor("#FEE2E2")))
                env_style.append(("TEXTCOLOR", (4,i),(4,i), colors.HexColor("#991B1B")))
            elif e["status"] == "warn":
                env_style.append(("BACKGROUND",(4,i),(4,i), colors.HexColor("#FEF3C7")))

        t_env.setStyle(TableStyle(env_style))
        story.append(t_env)

        doc.build(story)
        return buf.getvalue()

    except ImportError:
        return _pdf_fallback_text("ReportLab niet geïnstalleerd.")
    except Exception as exc:
        return _pdf_fallback_text(str(exc))


def _pdf_fallback_text(reden: str) -> bytes:
    """Minimale bytes als PDF niet kan worden gegenereerd."""
    msg = f"%PDF-1.4\n% PDF generatie mislukt: {reden}"
    return msg.encode()
