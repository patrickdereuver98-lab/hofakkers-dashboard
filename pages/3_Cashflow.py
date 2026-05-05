"""
pages/3_Cashflow.py  –  Hofakkers 44
Maandelijkse cashflow planner – volledig bewerkbaar.
"""
import streamlit as st
import pandas as pd
import plotly.graph_objects as go

from utils.ui import page_setup, header, kpi, progress, sidebar
from utils.state import (
    init, calc_maand_totalen, calc_project, maand, set_maand,
    dash, set_dashboard,
)
from utils.config import CHART_COLORS
from utils.excel_handler import save_maand as excel_save_maand, save_dashboard

page_setup("💳 Cashflow – Hofakkers 44")
init()

sidebar(calc_maand_totalen(), calc_project())
header("💳 Maandelijkse Cashflow", "Inkomsten & Uitgaven · Volledig bewerkbaar")

mt = calc_maand_totalen()

# ── KPI rij ─────────────────────────────────────────────────────────────────
c1, c2, c3, c4, c5 = st.columns(5)
with c1:  kpi("💰 Inkomen",    f"€ {mt.get('inkomen',0):,.0f}",    "netto/maand")
with c2:  kpi("🏠 Vaste Lasten", f"€ {mt.get('vaste',0):,.0f}",    "wonen+verzek+vervoer")
with c3:  kpi("🛒 Variabel",   f"€ {mt.get('variabel',0):,.0f}",  "boodschappen+vrije tijd")
with c4:  kpi("💹 Sparen",     f"€ {mt.get('sparen',0):,.0f}",    "sparen+beleggen", "grn")
with c5:
    r = mt.get("ruimte", 0)
    kpi("🎯 Buffer", f"€ {r:,.0f}", "vrij per maand", "grn" if r >= 0 else "red")

st.markdown("---")

tabs = st.tabs(["📊 Overzicht", "✏️ Maandbegroting Bewerken", "⚙️ Toplevel Instellingen"])

# ── Tab 1: Overzicht ─────────────────────────────────────────────────────────
with tabs[0]:
    col_l, col_r = st.columns(2)
    with col_l:
        st.markdown("##### 🍩 Cashflow Donut")
        data_donut = {
            "Wonen & vaste lasten": mt.get("vaste", 0),
            "Variabele lasten":     mt.get("variabel", 0),
            "Sparen & beleggen":    mt.get("sparen", 0),
            "Buffer":               max(mt.get("ruimte", 0), 0),
        }
        data_donut = {k: v for k, v in data_donut.items() if v > 0}
        if data_donut:
            fig = go.Figure(go.Pie(
                labels=list(data_donut.keys()),
                values=list(data_donut.values()),
                hole=0.58,
                marker_colors=["#FF8C00","#FFD700","#10B981","#3B82F6"],
                textinfo="label+percent+value",
                hovertemplate="<b>%{label}</b><br>€ %{value:,.0f}/maand<br>%{percent}<extra></extra>",
            ))
            fig.update_layout(
                plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
                showlegend=False,
                margin=dict(l=0,r=0,t=0,b=0), height=340,
                annotations=[dict(
                    text=f"<b>€ {mt.get('inkomen',0):,.0f}</b><br>/maand",
                    x=0.5, y=0.5, font_size=12, showarrow=False,
                )],
            )
            st.plotly_chart(fig, use_container_width=True)

    with col_r:
        st.markdown("##### 📊 Procentueel van Inkomen")
        ink = mt.get("inkomen", 1)
        items = [
            ("🏠 Vaste Lasten",     mt.get("vaste",0),    ""),
            ("🛒 Variabele Lasten", mt.get("variabel",0),  ""),
            ("💹 Sparen",           mt.get("sparen",0),   "grn"),
            ("🎯 Buffer",           max(mt.get("ruimte",0),0), "grn"),
        ]
        for lbl, bedrag, variant in items:
            pct = bedrag / ink * 100 if ink else 0
            progress(f"{lbl}  (€ {bedrag:,.0f})", pct, variant)

        st.markdown("---")
        ink_j = mt.get("inkomen",0) * 12
        uit_j = mt.get("totaal_uitgaven",0) * 12
        st.markdown("##### 📅 Jaarperspectief")
        j1, j2, j3 = st.columns(3)
        j1.metric("Jaarinkomen",  f"€ {ink_j:,.0f}")
        j2.metric("Jaaruitgaven", f"€ {uit_j:,.0f}")
        j3.metric("Jaarruimte",   f"€ {(ink_j-uit_j):,.0f}")

    # Detailtabel maandbegroting
    st.markdown("---")
    st.markdown("##### 📋 Detail Maandbegroting")
    rows = maand()
    if rows:
        df_m = pd.DataFrame(rows)
        if "Bedrag (€)" in df_m.columns:
            df_m["Bedrag (€)"] = pd.to_numeric(df_m["Bedrag (€)"], errors="coerce").fillna(0)
        st.dataframe(
            df_m.style.format({"Bedrag (€)": "€ {:,.2f}"}),
            use_container_width=True,
            height=400,
            hide_index=True,
        )

# ── Tab 2: Maandbegroting Bewerken ────────────────────────────────────────────
with tabs[1]:
    st.markdown("##### ✏️ Maandbegroting bewerken")
    st.caption("Pas posten aan, voeg toe of verwijder. Categorieën: WONEN, VERZEKERINGEN, VERVOER, BOODSCHAPPEN, PERSOONLIJK, VRIJETIJD, SPAREN, INKOMSTEN")

    rows = maand()
    df_edit = pd.DataFrame(rows) if rows else pd.DataFrame(
        columns=["Categorie","Post","Bedrag (€)"]
    )

    edited = st.data_editor(
        df_edit,
        column_config={
            "Categorie":  st.column_config.TextColumn("Categorie", width="medium"),
            "Post":       st.column_config.TextColumn("Post",      width="large"),
            "Bedrag (€)": st.column_config.NumberColumn("Bedrag (€)", format="€ %.2f", min_value=0),
        },
        num_rows="dynamic",
        use_container_width=True,
        height=450,
        key="editor_maand",
    )

    c1b, c2b = st.columns(2)
    with c1b:
        if st.button("💾 Opslaan in App", type="primary", use_container_width=True):
            set_maand(edited.to_dict(orient="records"))
            st.success("✅ Maandbegroting bijgewerkt!")
            st.rerun()
    with c2b:
        if st.button("💾 Naar Excel", use_container_width=True):
            set_maand(edited.to_dict(orient="records"))
            if excel_save_maand(edited.to_dict(orient="records")):
                st.success("✅ Opgeslagen!")
            else:
                st.error("❌ Mislukt.")

# ── Tab 3: Toplevel Instellingen ──────────────────────────────────────────────
with tabs[2]:
    st.markdown("##### ⚙️ Toplevel Cashflow Instellingen (Dashboard PRO)")
    st.caption("Deze waarden komen direct uit het 'Dashboard PRO' tabblad in de Excel.")

    dashboard = dash()
    cashflow_keys = [
        "Netto inkomen per maand",
        "Vaste lasten per maand (wonen + verzekeringen + vervoer)",
        "Variabele lasten per maand (boodschappen + vrijetijd)",
        "Sparen & beleggen per maand",
        "Totaal uitgaven incl. sparen",
        "Ruimte per maand (incl. sparen)",
        "Ruimte per maand excl. sparen",
    ]

    for key in cashflow_keys:
        if key in dashboard:
            new_val = st.number_input(
                key, value=float(dashboard.get(key, 0)), step=50.0,
                format="%.2f", key=f"cf_{key}",
            )
            dashboard[key] = new_val

    if st.button("💾 Cashflow instellingen opslaan", type="primary"):
        set_dashboard(dashboard)
        if save_dashboard(dashboard):
            st.success("✅ Opgeslagen naar Excel!")
        else:
            st.success("✅ Bijgewerkt in app!")
        st.rerun()
