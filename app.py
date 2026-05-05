"""
app.py  –  Hofakkers 44 Renovatie Dashboard
Landingspagina: volledig overzicht vanuit de echte Excel.

BUGS FIXED:
- CHART_COLORS: correct geïmporteerd (lijst, niet dict)
- KPI-aanroepen: correcte veld-keys (project['verbouwing'] etc.)
- maand_tot-keys: inkomen/vaste/variabel/sparen/ruimte/totaal_uitgaven
- Donut-charts: correct geconfigureerd met annotations
- calc_spaargeld: correcte keys (patrick/willianne/samen/totaal_sparen)
"""
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px

from utils.ui import page_setup, header, kpi, progress, sidebar
from utils.state import (
    init, dash, set_dashboard,
    calc_maand_totalen, calc_project,
    calc_verbouwing_totalen, calc_inboedel_totalen,
    calc_spaargeld, save_all_to_excel,
)
from utils.config import CHART_COLORS
from utils.excel_handler import save_dashboard

# ── Bootstrap ───────────────────────────────────────────────────────────────
page_setup("🏠 Hofakkers 44 – Dashboard")
init()

maand_tot = calc_maand_totalen()
project   = calc_project()
verb_tot  = calc_verbouwing_totalen()
inbo_tot  = calc_inboedel_totalen()
verm      = calc_spaargeld()

sidebar(maand_tot, project)

# ── Header ──────────────────────────────────────────────────────────────────
header(
    "Hofakkers 44 – Renovatie Dashboard",
    "Real-time financieel overzicht · Patrick & Willianne · Alles aanpasbaar",
    "🏠",
)

# ══════════════════════════════════════════════════════════════════════════════
# SECTIE 1 – PROJECT KPI's
# ══════════════════════════════════════════════════════════════════════════════
st.markdown("### 📊 Project Overzicht")
c1, c2, c3, c4, c5 = st.columns(5)
with c1:
    kpi("🔨 Verbouwing",      f"€ {project['verbouwing']:,.0f}",  "begroting totaal")
with c2:
    kpi("🛋️ Inboedel",        f"€ {project['inboedel']:,.0f}",    "begroting totaal")
with c3:
    kpi("📦 Totaal Project",  f"€ {project['project']:,.0f}",     "verbouwing + inboedel")
with c4:
    kpi("👤 Per Persoon",     f"€ {project['per_persoon']:,.0f}", "benodigd", "blu")
with c5:
    samen = project["samen"]
    kpi("💎 Resterend Samen", f"€ {samen:,.0f}", "na verbouwing",
        "grn" if samen >= 0 else "red")

st.markdown("<br>", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# SECTIE 2 – MAAND CASHFLOW KPI's
# ══════════════════════════════════════════════════════════════════════════════
st.markdown("### 💳 Maandelijkse Cashflow")
m1, m2, m3, m4, m5 = st.columns(5)
ink    = maand_tot.get("inkomen", 0)
vaste  = maand_tot.get("vaste", 0)
var    = maand_tot.get("variabel", 0)
spar   = maand_tot.get("sparen", 0)
ruimte = maand_tot.get("ruimte", 0)

with m1: kpi("💰 Netto Inkomen",     f"€ {ink:,.0f}",    "per maand")
with m2: kpi("🏠 Vaste Lasten",      f"€ {vaste:,.0f}",  "wonen + verzek + vervoer")
with m3: kpi("🛒 Variabele Lasten",  f"€ {var:,.0f}",    "boodschappen + vrije tijd")
with m4: kpi("💹 Sparen & Beleggen", f"€ {spar:,.0f}",   "per maand", "grn")
with m5: kpi("🎯 Buffer / Ruimte",   f"€ {ruimte:,.0f}", "vrij na alles",
             "grn" if ruimte >= 0 else "red")

if ink > 0:
    pct_uit = maand_tot.get("totaal_uitgaven", 0) / ink * 100
    progress(f"Uitnutting inkomen ({pct_uit:.1f}%)", pct_uit)

st.markdown("---")

# ══════════════════════════════════════════════════════════════════════════════
# SECTIE 3 – VERBOUWING + INBOEDEL DONUTS
# ══════════════════════════════════════════════════════════════════════════════
col_l, col_r = st.columns(2)

with col_l:
    st.markdown("#### 🔨 Verbouwing per Categorie")
    cats_v = verb_tot.get("categorieën", {})
    if cats_v:
        fig = go.Figure(go.Pie(
            labels=list(cats_v.keys()),
            values=list(cats_v.values()),
            hole=0.55,
            marker_colors=CHART_COLORS,
            textinfo="label+percent",
            hovertemplate="<b>%{label}</b><br>€ %{value:,.0f}<br>%{percent}<extra></extra>",
        ))
        fig.update_layout(
            plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
            showlegend=True, legend=dict(orientation="h", y=-0.28),
            margin=dict(l=0, r=0, t=10, b=70), height=360,
            annotations=[dict(
                text=f"<b>€ {verb_tot['totaal']:,.0f}</b>",
                x=0.5, y=0.5, font_size=14, font_color="#1A1A2E",
                showarrow=False,
            )],
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Geen verbouwingsdata geladen uit Excel.")

with col_r:
    st.markdown("#### 🛋️ Inboedel per Categorie")
    cats_i = inbo_tot.get("categorieën", {})
    if cats_i:
        fig2 = go.Figure(go.Pie(
            labels=list(cats_i.keys()),
            values=list(cats_i.values()),
            hole=0.55,
            marker_colors=CHART_COLORS[2:] + CHART_COLORS[:2],
            textinfo="label+percent",
            hovertemplate="<b>%{label}</b><br>€ %{value:,.0f}<br>%{percent}<extra></extra>",
        ))
        fig2.update_layout(
            plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
            showlegend=True, legend=dict(orientation="h", y=-0.28),
            margin=dict(l=0, r=0, t=10, b=70), height=360,
            annotations=[dict(
                text=f"<b>€ {inbo_tot['totaal']:,.0f}</b>",
                x=0.5, y=0.5, font_size=14, font_color="#1A1A2E",
                showarrow=False,
            )],
        )
        st.plotly_chart(fig2, use_container_width=True)
    else:
        st.info("Geen inboedeldata geladen uit Excel.")

st.markdown("---")

# ══════════════════════════════════════════════════════════════════════════════
# SECTIE 4 – CASHFLOW DONUT + VERMOGEN
# ══════════════════════════════════════════════════════════════════════════════
col_c, col_v = st.columns([3, 2])

with col_c:
    st.markdown("#### 📅 Maandbudget Verdeling")
    cats_maand = {
        "Wonen & vast":    vaste,
        "Variabel":        var,
        "Sparen":          spar,
        "Buffer":          max(ruimte, 0),
    }
    cats_maand = {k: v for k, v in cats_maand.items() if v > 0}
    if cats_maand:
        fig3 = go.Figure(go.Pie(
            labels=list(cats_maand.keys()),
            values=list(cats_maand.values()),
            hole=0.55,
            marker_colors=["#FF8C00", "#FFD700", "#10B981", "#3B82F6"],
            textinfo="label+percent",
            hovertemplate="<b>%{label}</b><br>€ %{value:,.0f}/maand<extra></extra>",
        ))
        fig3.update_layout(
            plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
            showlegend=True, legend=dict(orientation="h", y=-0.25),
            margin=dict(l=0, r=0, t=10, b=60), height=320,
            annotations=[dict(
                text=f"<b>€ {ink:,.0f}</b><br>/maand",
                x=0.5, y=0.5, font_size=12, font_color="#1A1A2E",
                showarrow=False,
            )],
        )
        st.plotly_chart(fig3, use_container_width=True)
    else:
        st.info("Geen cashflow-data. Controleer 'Maandbegroting' sheet of vul Projectinstellingen in.")

with col_v:
    st.markdown("#### 💎 Vermogen na Verbouwing")
    st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)
    kpi("👤 Patrick",     f"€ {verm['patrick']:,.0f}",       "resterend vermogen", "blu")
    st.markdown("<div style='height:10px'></div>", unsafe_allow_html=True)
    kpi("👤 Willianne",   f"€ {verm['willianne']:,.0f}",     "resterend vermogen", "grn")
    st.markdown("<div style='height:10px'></div>", unsafe_allow_html=True)
    kpi("💎 Samen",       f"€ {verm['samen']:,.0f}",         "gezamenlijk")
    st.markdown("<div style='height:10px'></div>", unsafe_allow_html=True)
    kpi("🏦 Nu Gespaard", f"€ {verm['totaal_sparen']:,.0f}", "sparen + beleggen")

st.markdown("---")

# ══════════════════════════════════════════════════════════════════════════════
# SECTIE 5 – VERBOUWING HORIZONTALE BAR
# ══════════════════════════════════════════════════════════════════════════════
st.markdown("#### 🏗️ Verbouwing – Budget per Categorie")
cats_v = verb_tot.get("categorieën", {})
if cats_v:
    df_bar = pd.DataFrame({
        "Categorie": list(cats_v.keys()),
        "Bedrag (€)": list(cats_v.values()),
    }).sort_values("Bedrag (€)", ascending=True)

    fig4 = go.Figure(go.Bar(
        x=df_bar["Bedrag (€)"],
        y=df_bar["Categorie"],
        orientation="h",
        marker=dict(
            color=df_bar["Bedrag (€)"],
            colorscale=[[0, "#FFD700"], [1, "#FF8C00"]],
            showscale=False,
        ),
        text=df_bar["Bedrag (€)"].apply(lambda x: f"€ {x:,.0f}"),
        textposition="outside",
        hovertemplate="<b>%{y}</b><br>€ %{x:,.0f}<extra></extra>",
    ))
    fig4.update_layout(
        plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
        xaxis=dict(showgrid=True, gridcolor="#F3F4F6", tickprefix="€"),
        yaxis=dict(showgrid=False),
        margin=dict(l=0, r=100, t=10, b=0),
        height=max(240, len(cats_v) * 42),
        font=dict(family="Inter"),
    )
    st.plotly_chart(fig4, use_container_width=True)

st.markdown("---")

# ══════════════════════════════════════════════════════════════════════════════
# SECTIE 6 – INBOEDEL HORIZONTALE BAR
# ══════════════════════════════════════════════════════════════════════════════
st.markdown("#### 🛋️ Inboedel – Budget per Kamer")
cats_i = inbo_tot.get("categorieën", {})
if cats_i:
    df_bar2 = pd.DataFrame({
        "Kamer": list(cats_i.keys()),
        "Bedrag (€)": list(cats_i.values()),
    }).sort_values("Bedrag (€)", ascending=True)

    fig5 = go.Figure(go.Bar(
        x=df_bar2["Bedrag (€)"],
        y=df_bar2["Kamer"],
        orientation="h",
        marker=dict(
            color=df_bar2["Bedrag (€)"],
            colorscale=[[0, "#3B82F6"], [1, "#10B981"]],
            showscale=False,
        ),
        text=df_bar2["Bedrag (€)"].apply(lambda x: f"€ {x:,.0f}"),
        textposition="outside",
        hovertemplate="<b>%{y}</b><br>€ %{x:,.0f}<extra></extra>",
    ))
    fig5.update_layout(
        plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
        xaxis=dict(showgrid=True, gridcolor="#F3F4F6", tickprefix="€"),
        yaxis=dict(showgrid=False),
        margin=dict(l=0, r=100, t=10, b=0),
        height=max(240, len(cats_i) * 42),
        font=dict(family="Inter"),
    )
    st.plotly_chart(fig5, use_container_width=True)

st.markdown("---")

# ══════════════════════════════════════════════════════════════════════════════
# SECTIE 7 – BEWERKBARE PROJECTINSTELLINGEN
# ══════════════════════════════════════════════════════════════════════════════
with st.expander("⚙️ Projectinstellingen aanpassen (Dashboard PRO)", expanded=False):
    st.caption("Alle waarden komen uit 'Dashboard PRO' in de Excel. Wijzig en sla op.")
    d_data = dash()
    if d_data:
        df_dash = pd.DataFrame(
            list(d_data.items()),
            columns=["Instelling", "Waarde"],
        )
        edited = st.data_editor(
            df_dash,
            column_config={
                "Instelling": st.column_config.TextColumn("Instelling", width="large",  disabled=True),
                "Waarde":     st.column_config.TextColumn("Waarde",     width="medium"),
            },
            num_rows="dynamic",
            use_container_width=True,
            key="editor_dash_main",
        )
        if st.button("💾 Instellingen opslaan", type="primary", key="save_dash_main"):
            new_d = {}
            for _, row in edited.iterrows():
                k = str(row["Instelling"]).strip()
                v = row["Waarde"]
                if k and k.lower() != "nan":
                    try:
                        new_d[k] = float(str(v).replace(",", ".").replace("€", "").strip())
                    except (TypeError, ValueError):
                        new_d[k] = v
            set_dashboard(new_d)
            if save_dashboard(new_d):
                st.success("✅ Opgeslagen naar Excel!")
            else:
                st.success("✅ Bijgewerkt in app!")
            st.rerun()
    else:
        st.info("Geen dashboard-data gevonden. Controleer of de Excel het tabblad 'Dashboard PRO' bevat.")

# ── Global save ──────────────────────────────────────────────────────────────
st.markdown("---")
col_sv, _ = st.columns([2, 5])
with col_sv:
    if st.button("💾 Alles opslaan naar Excel", type="primary", use_container_width=True):
        if save_all_to_excel():
            st.success("✅ Volledig opgeslagen!")
        else:
            st.error("❌ Opslaan mislukt.")
