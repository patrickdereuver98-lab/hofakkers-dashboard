"""
pages/3_Cashflow.py  –  Hofakkers 44  v3.0
"""
import streamlit as st
import pandas as pd
import plotly.graph_objects as go

from utils.ui import page_setup, header, kpi, progress, sidebar, alert, sec_div
from utils.notifications import render_notification_bar
from utils.state import (
    init, calc_maand_totalen, calc_project,
    maand, set_maand, dash, set_dashboard,
)
from utils.config import CHART_COLORS
from utils.excel_handler import save_maand as excel_save_maand, save_dashboard

page_setup("💳 Cashflow – Hofakkers 44")
init()

sidebar(calc_maand_totalen(), calc_project())
header("💳 Maandelijkse Cashflow", "YNAB-stijl · Elke maand-euro heeft een bestemming", "💳")

render_notification_bar(max_visible=2, filter_page="Cashflow")

mt = calc_maand_totalen()
ink    = mt.get("inkomen", 0)
vaste  = mt.get("vaste", 0)
var    = mt.get("variabel", 0)
spar   = mt.get("sparen", 0)
ruimte = mt.get("ruimte", 0)
totuit = mt.get("totaal_uitgaven", 0)

c1, c2, c3, c4, c5 = st.columns(5)
with c1: kpi("💰 Netto Inkomen",     f"€ {ink:,.0f}",   "/maand", "neu")
with c2: kpi("🏠 Vaste Lasten",      f"€ {vaste:,.0f}",  f"{vaste/ink*100:.0f}% van inkomen" if ink else "")
with c3: kpi("🛒 Variabele Lasten",  f"€ {var:,.0f}",    f"{var/ink*100:.0f}% van inkomen"   if ink else "")
with c4: kpi("💹 Sparen & Beleggen", f"€ {spar:,.0f}",   f"{spar/ink*100:.0f}% van inkomen"  if ink else "", "grn")
with c5:
    kpi("🎯 Vrije Buffer", f"€ {ruimte:,.0f}",
        "✓ positief saldo" if ruimte >= 0 else "⚠️ negatief saldo",
        "grn" if ruimte >= 0 else "red")

if ink > 0:
    st.markdown("")
    progress(f"🏠 Vaste lasten  (€ {vaste:,.0f})", vaste/ink*100)
    progress(f"🛒 Variabel       (€ {var:,.0f})",    var/ink*100)
    progress(f"💹 Sparen         (€ {spar:,.0f})",   spar/ink*100)

    besteed_pct = totuit / ink * 100
    if besteed_pct > 100:
        alert(f"⚠️ Uitgaven ({besteed_pct:.0f}%) overstijgen het inkomen! Review je budgetten.", "red")
    elif besteed_pct > 85:
        alert(f"⚠️ {besteed_pct:.0f}% van inkomen toegewezen — weinig ruimte voor onverwachte kosten.", "warn")
    else:
        alert(f"✓ {100-besteed_pct:.0f}% van inkomen (€ {ruimte:,.0f}) is vrij besteedbaar.", "grn")

st.markdown("---")

tabs = st.tabs(["📊 Overzicht", "✏️ Maandbegroting Bewerken", "⚙️ Toplevel Instellingen"])

# ── Tab 1: Overzicht ──────────────────────────────────────────────────────
with tabs[0]:
    col_l, col_r = st.columns(2)

    with col_l:
        sec_div("Verdeling van Inkomen", "🍩")
        data_d = {"Wonen & vast":vaste,"Variabel":var,"Sparen":spar,"Buffer":max(ruimte,0)}
        data_d = {k:v for k,v in data_d.items() if v > 0}
        if data_d:
            fig = go.Figure(go.Pie(
                labels=list(data_d.keys()), values=list(data_d.values()),
                hole=0.58, marker_colors=["#FF8C00","#FFD700","#10B981","#3B82F6"],
                textinfo="label+percent",
                hovertemplate="<b>%{label}</b><br>€ %{value:,.0f}/maand<extra></extra>",
            ))
            fig.update_layout(
                plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
                showlegend=True, legend=dict(orientation="h",y=-0.25),
                margin=dict(l=0,r=0,t=0,b=60), height=340,
                annotations=[dict(text=f"<b>€{ink:,.0f}</b><br>/maand",
                                  x=0.5,y=0.5,font_size=12,showarrow=False)],
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            alert("Vul cashflow-instellingen in via Toplevel Instellingen.", "warn")

    with col_r:
        sec_div("Jaarperspectief", "📅")
        st.markdown("<br>", unsafe_allow_html=True)
        ink_j  = ink * 12
        uit_j  = totuit * 12
        spar_j = spar * 12
        vrij_j = ruimte * 12

        kpi("📅 Jaarinkomen",  f"€ {ink_j:,.0f}",  "/jaar")
        st.markdown("<div style='height:6px'></div>", unsafe_allow_html=True)
        kpi("📤 Jaaruitgaven", f"€ {uit_j:,.0f}",  "incl. sparen")
        st.markdown("<div style='height:6px'></div>", unsafe_allow_html=True)
        kpi("💹 Jaarsparen",   f"€ {spar_j:,.0f}", "naar spaarrekening", "grn")
        st.markdown("<div style='height:6px'></div>", unsafe_allow_html=True)
        kpi("🎯 Jaarruimte",   f"€ {vrij_j:,.0f}",
            "✓ buffer" if vrij_j >= 0 else "⚠️ tekort",
            "grn" if vrij_j >= 0 else "red")

    st.markdown("---")
    sec_div("Detail Maandbegroting", "📋")
    rows = maand()
    if rows:
        df_m = pd.DataFrame(rows)
        if "Bedrag (€)" in df_m.columns:
            df_m["Bedrag (€)"] = pd.to_numeric(df_m["Bedrag (€)"], errors="coerce").fillna(0)
        st.dataframe(df_m.style.format({"Bedrag (€)":"€ {:,.2f}"}),
                     use_container_width=True, height=400, hide_index=True)
        totaal_m = df_m["Bedrag (€)"].sum() if "Bedrag (€)" in df_m.columns else 0
        st.metric("Totaal geregistreerde bedragen", f"€ {totaal_m:,.2f}")
    else:
        alert("Geen maandbegroting-data. Controleer tabblad 'Maandbegroting' in Excel.", "warn")

# ── Tab 2: Bewerken ───────────────────────────────────────────────────────
with tabs[1]:
    sec_div("Maandbegroting bewerken", "✏️")
    rows = maand()
    df_edit = pd.DataFrame(rows) if rows else pd.DataFrame(columns=["Categorie","Post","Bedrag (€)"])
    for col in ["Categorie","Post","Bedrag (€)"]:
        if col not in df_edit.columns:
            df_edit[col] = "" if col != "Bedrag (€)" else 0.0

    edited = st.data_editor(
        df_edit[["Categorie","Post","Bedrag (€)"]],
        column_config={
            "Categorie":  st.column_config.TextColumn("Categorie",  width="medium"),
            "Post":       st.column_config.TextColumn("Post",       width="large"),
            "Bedrag (€)": st.column_config.NumberColumn("Bedrag (€)", format="€ %.2f", min_value=0),
        },
        num_rows="dynamic", use_container_width=True, height=460, key="editor_maand",
    )
    nieuw_tot = float(pd.to_numeric(edited["Bedrag (€)"], errors="coerce").fillna(0).sum())
    st.metric("Nieuw Totaal geregistreerd", f"€ {nieuw_tot:,.2f}")

    if st.button("💾 Opslaan naar Excel", type="primary",
                 use_container_width=True, key="maand_save"):
        rows_new = edited.to_dict(orient="records")
        set_maand(rows_new)
        if excel_save_maand(rows_new):
            st.success("✅ Opgeslagen naar Excel (backup gemaakt)")
            st.rerun()
        else:
            st.error("❌ Mislukt — is Excel geopend?")

# ── Tab 3: Toplevel ───────────────────────────────────────────────────────
with tabs[2]:
    sec_div("Cashflow Instellingen (Dashboard PRO)", "⚙️")
    st.caption("Directe koppeling met 'Dashboard PRO' tabblad in de Excel.")

    dashboard = dict(dash())
    cashflow_keys = [
        "Netto inkomen per maand",
        "Vaste lasten per maand (wonen + verzekeringen + vervoer)",
        "Variabele lasten per maand (boodschappen + vrijetijd)",
        "Sparen & beleggen per maand",
        "Totaal uitgaven incl. sparen",
        "Ruimte per maand (incl. sparen)",
        "Ruimte per maand excl. sparen",
    ]
    aanwezig = [k for k in cashflow_keys if k in dashboard]
    if aanwezig:
        cols_cf = st.columns(2)
        for i, key in enumerate(aanwezig):
            with cols_cf[i % 2]:
                try:
                    cur = float(str(dashboard.get(key,0)).replace(",",".").replace("€",""))
                except (TypeError, ValueError):
                    cur = 0.0
                new_v = st.number_input(key, value=cur, step=50.0, format="%.2f", key=f"cf_{key}")
                dashboard[key] = new_v

        if st.button("💾 Opslaan naar Excel", type="primary", key="cf_save"):
            set_dashboard(dashboard)
            if save_dashboard(dashboard):
                st.success("✅ Opgeslagen naar Excel (backup gemaakt)")
                st.rerun()
            else:
                st.error("❌ Mislukt.")
    else:
        alert("Geen cashflow-instellingen gevonden in 'Dashboard PRO'.", "warn")
