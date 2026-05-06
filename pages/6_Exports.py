"""
pages/6_Exports.py  –  Hofakkers 44  v4.0
Alles wat je kunt downloaden, altijd actueel op basis van session_state.
"""
import streamlit as st
from datetime import date

from utils.ui import page_setup, header, kpi, sidebar, alert, sec_div
from utils.state import init, calc_maand_totalen, calc_project, calc_ynab_envelopes
from utils.exports import (
    export_verbouwing_csv, export_inboedel_csv,
    export_kosten_csv, export_planning_csv,
    export_ynab_csv, export_full_excel,
    export_all_zip, export_ynab_pdf,
)
from utils.notifications import render_notification_bar
import pandas as pd

page_setup("📤 Exports – Hofakkers 44")
init()

sidebar(calc_maand_totalen(), calc_project())
header("📤 Exports & Downloads",
       "Altijd actueel · Gebaseerd op huidige dashboard-data", "📤")

render_notification_bar(max_visible=2, filter_page="")

ts = date.today().strftime("%d-%m-%Y")

# ── KPI's: snelle status ──────────────────────────────────────────────────
verb = st.session_state.get("verbouwing", pd.DataFrame())
inbo = st.session_state.get("inboedel",   pd.DataFrame())
kost = st.session_state.get("kosten",     pd.DataFrame())
plan = st.session_state.get("planning",   [])

c1, c2, c3, c4 = st.columns(4)
with c1: kpi("🔨 Verbouwing posten", str(len(verb)) if not verb.empty else "0", "regels")
with c2: kpi("🛋️ Inboedel posten",  str(len(inbo)) if not inbo.empty else "0", "regels")
with c3: kpi("🧾 Kosten regels",
             str(len(kost)) if isinstance(kost, pd.DataFrame) and not kost.empty else "0")
with c4: kpi("📅 Planning stappen", str(len(plan)))

st.markdown("---")

# ══════════════════════════════════════════════════════════════════════════════
# 1. ALLES IN ÉÉN
# ══════════════════════════════════════════════════════════════════════════════
sec_div("Alles in één download", "📦")

col_zip, col_xl = st.columns(2)

with col_zip:
    with st.container(border=True):
        st.markdown("#### 🗜️ Volledig ZIP-pakket")
        st.caption("Bevat: alle CSVs + volledig Excel-rapport. Ideaal voor archivering.")
        st.markdown("")
        if st.button("📦 Genereer ZIP", type="primary", use_container_width=True, key="gen_zip"):
            with st.spinner("ZIP samenstellen..."):
                zip_bytes = export_all_zip()
            st.download_button(
                label=f"⬇️ Download ZIP ({ts})",
                data=zip_bytes,
                file_name=f"hofakkers44_{date.today().strftime('%Y%m%d')}_export.zip",
                mime="application/zip",
                use_container_width=True,
            )

with col_xl:
    with st.container(border=True):
        st.markdown("#### 📊 Volledig Excel Rapport")
        st.caption("Gestructureerd overzicht: Samenvatting · YNAB · Verbouwing · Inboedel · Kosten · Planning.")
        st.markdown("")
        if st.button("📊 Genereer Excel", type="primary", use_container_width=True, key="gen_xl"):
            with st.spinner("Excel samenstellen..."):
                xl_bytes = export_full_excel()
            st.download_button(
                label=f"⬇️ Download Excel ({ts})",
                data=xl_bytes,
                file_name=f"hofakkers44_{date.today().strftime('%Y%m%d')}_rapport.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True,
            )

st.markdown("---")

# ══════════════════════════════════════════════════════════════════════════════
# 2. INDIVIDUELE EXPORTS
# ══════════════════════════════════════════════════════════════════════════════
sec_div("Individuele Downloads", "📄")

tabs = st.tabs([
    "💰 YNAB Rapport",
    "🔨 Verbouwing",
    "🛋️ Inboedel",
    "🧾 Kosten",
    "📅 Planning",
])

# ── YNAB PDF + CSV ──────────────────────────────────────────────────────────
with tabs[0]:
    col_pdf, col_csv = st.columns(2)

    with col_pdf:
        with st.container(border=True):
            st.markdown("#### 📄 YNAB PDF Rapport")
            st.caption("Overzicht van alle envelopes, budgetten en vrije buffer. "
                       "Geschikt voor printen of delen.")

            # Preview
            try:
                ynab = calc_ynab_envelopes()
                st.markdown(f"**Vrije buffer:** € {ynab['vrij']:,.0f}")
                st.markdown(f"**Totaal toegewezen:** € {ynab['toegewezen']:,.0f}")
                st.markdown(f"**Envelopes:** {len(ynab['envelopes'])}")
                over = [e for e in ynab["envelopes"] if e["status"] == "over"]
                if over:
                    alert(f"⚠️ {len(over)} envelope(s) over budget — rood gemarkeerd in PDF.", "warn")
            except Exception:
                pass

            if st.button("📄 Genereer PDF", type="primary",
                         use_container_width=True, key="gen_pdf"):
                with st.spinner("PDF genereren..."):
                    pdf_bytes = export_ynab_pdf()
                st.download_button(
                    label=f"⬇️ Download PDF ({ts})",
                    data=pdf_bytes,
                    file_name=f"hofakkers44_{date.today().strftime('%Y%m%d')}_ynab.pdf",
                    mime="application/pdf",
                    use_container_width=True,
                )

    with col_csv:
        with st.container(border=True):
            st.markdown("#### 📋 YNAB CSV")
            st.caption("Alle envelopes als CSV — te importeren in Excel, Google Sheets etc.")

            csv_ynab = export_ynab_csv()
            st.download_button(
                label=f"⬇️ YNAB CSV ({ts})",
                data=csv_ynab,
                file_name=f"hofakkers44_{date.today().strftime('%Y%m%d')}_ynab.csv",
                mime="text/csv",
                use_container_width=True,
                key="dl_ynab_csv",
            )

            # Preview
            try:
                import io
                df_prev = pd.read_csv(io.BytesIO(csv_ynab), encoding="utf-8-sig")
                st.dataframe(df_prev.head(8), use_container_width=True,
                             hide_index=True, height=220)
            except Exception:
                pass

# ── Verbouwing ───────────────────────────────────────────────────────────────
with tabs[1]:
    col_a, col_b = st.columns(2)
    with col_a:
        with st.container(border=True):
            st.markdown("#### 🔨 Verbouwing CSV")
            csv_v = export_verbouwing_csv()
            st.download_button(
                label=f"⬇️ Verbouwing CSV ({ts})",
                data=csv_v,
                file_name=f"hofakkers44_{date.today().strftime('%Y%m%d')}_verbouwing.csv",
                mime="text/csv", use_container_width=True, key="dl_verb_csv",
            )
    with col_b:
        with st.container(border=True):
            st.markdown("#### 👀 Preview")
            if not verb.empty:
                st.dataframe(verb.head(8), use_container_width=True,
                             hide_index=True, height=240)
            else:
                alert("Geen verbouwingsdata.", "warn")

# ── Inboedel ────────────────────────────────────────────────────────────────
with tabs[2]:
    col_a, col_b = st.columns(2)
    with col_a:
        with st.container(border=True):
            st.markdown("#### 🛋️ Inboedel CSV")
            csv_i = export_inboedel_csv()
            st.download_button(
                label=f"⬇️ Inboedel CSV ({ts})",
                data=csv_i,
                file_name=f"hofakkers44_{date.today().strftime('%Y%m%d')}_inboedel.csv",
                mime="text/csv", use_container_width=True, key="dl_inbo_csv",
            )
    with col_b:
        with st.container(border=True):
            st.markdown("#### 👀 Preview")
            if not inbo.empty:
                st.dataframe(inbo.head(8), use_container_width=True,
                             hide_index=True, height=240)
            else:
                alert("Geen inboedeldata.", "warn")

# ── Kosten ───────────────────────────────────────────────────────────────────
with tabs[3]:
    col_a, col_b = st.columns(2)
    with col_a:
        with st.container(border=True):
            st.markdown("#### 🧾 Kosten CSV")
            csv_k = export_kosten_csv()
            st.download_button(
                label=f"⬇️ Kosten CSV ({ts})",
                data=csv_k,
                file_name=f"hofakkers44_{date.today().strftime('%Y%m%d')}_kosten.csv",
                mime="text/csv", use_container_width=True, key="dl_kost_csv",
            )
    with col_b:
        with st.container(border=True):
            st.markdown("#### 👀 Preview")
            if isinstance(kost, pd.DataFrame) and not kost.empty:
                st.dataframe(kost.head(8), use_container_width=True,
                             hide_index=True, height=240)
            else:
                alert("Nog geen kosten geregistreerd.", "blu")

# ── Planning ────────────────────────────────────────────────────────────────
with tabs[4]:
    col_a, col_b = st.columns(2)
    with col_a:
        with st.container(border=True):
            st.markdown("#### 📅 Planning CSV")
            csv_p = export_planning_csv()
            st.download_button(
                label=f"⬇️ Planning CSV ({ts})",
                data=csv_p,
                file_name=f"hofakkers44_{date.today().strftime('%Y%m%d')}_planning.csv",
                mime="text/csv", use_container_width=True, key="dl_plan_csv",
            )
    with col_b:
        with st.container(border=True):
            st.markdown("#### 👀 Preview")
            if plan:
                df_p = pd.DataFrame(plan)
                show = [c for c in ["Volgorde","Taak","Status","Deadline"] if c in df_p.columns]
                st.dataframe(df_p[show].head(10), use_container_width=True,
                             hide_index=True, height=280)
            else:
                alert("Geen planningsdata.", "blu")
