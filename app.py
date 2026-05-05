"""
app.py  –  Hofakkers 44 Renovatie Dashboard
Landingspagina: volledig overzicht van alle financiële data uit de Excel.
Alles aanpasbaar, geen harde getallen.
"""
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px

from utils.ui import page_setup, header, kpi, progress, sidebar
from utils.state import (
    init, dash, set_dashboard,
    calc_maand_totalen, calc_project, calc_verbouwing_totalen,
    calc_inboedel_totalen, calc_spaargeld, save_all_to_excel,
)
from utils.config import CHART_COLORS

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
    "🏠 Hofakkers 44 – Renovatie Dashboard",
    "Real-time financieel overzicht · Patrick & Willianne · Alles aanpasbaar"
)

# ══════════════════════════════════════════════════════════════════════════════
# SECTIE 1 – PROJECT KPI's
# ══════════════════════════════════════════════════════════════════════════════
st.markdown("### 📊 Project Overzicht")
c1, c2, c3, c4, c5 = st.columns(5)
with c1:
    kpi("🔨 Verbouwing",   f"€ {project['verbouwing']:,.0f}", "totaal begroting")
with c2:
    kpi("🛋️ Inboedel",    f"€ {project['inboedel']:,.0f}", "totaal begroting")
with c3:
    kpi("📦 Totaal project", f"€ {project['project']:,.0f}", "verbouwing + inboedel")
with c4:
    kpi("👤 Per persoon",  f"€ {project['per_persoon']:,.0f}", "benodigd", "blu")
with c5:
    samen = project['samen']
    kpi("💎 Samen resterend", f"€ {samen:,.0f}", "na verbouwing", "grn" if samen > 0 else "red")

st.markdown("<br>", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# SECTIE 2 – MAAND CASHFLOW KPI's
# ══════════════════════════════════════════════════════════════════════════════
st.markdown("### 💳 Maandelijkse Cashflow")
m1, m2, m3, m4, m5 = st.columns(5)
with m1:
    kpi("💰 Netto Inkomen",  f"€ {maand_tot.get('inkomen',0):,.0f}", "per maand")
with m2:
    kpi("🏠 Vaste Lasten",   f"€ {maand_tot.get('vaste',0):,.0f}", "wonen + verzek. + vervoer")
with m3:
    kpi("🛒 Variabele Lasten", f"€ {maand_tot.get('variabel',0):,.0f}", "boodschappen + vrijetijd")
with m4:
    kpi("💹 Sparen & Beleggen", f"€ {maand_tot.get('sparen',0):,.0f}", "per maand", "grn")
with m5:
    ruimte = maand_tot.get('ruimte', 0)
    kpi("🎯 Buffer / Ruimte", f"€ {ruimte:,.0f}", "vrij na alles", "grn" if ruimte >= 0 else "red")

# Uitnutting cashflow
if maand_tot.get("inkomen", 0) > 0:
    pct_uit = maand_tot.get("totaal_uitgaven", 0) / maand_tot["inkomen"] * 100
    progress(f"Uitnutting inkomen ({pct_uit:.1f}%)", pct_uit)

st.markdown("---")

# ══════════════════════════════════════════════════════════════════════════════
# SECTIE 3 – CHARTS (2 kolommen)
# ══════════════════════════════════════════════════════════════════════════════
col_l, col_r = st.columns(2)

# ── Verbouwing donut ────────────────────────────────────────────────────────
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
            showlegend=True, legend=dict(orientation="h", y=-0.25),
            margin=dict(l=0, r=0, t=0, b=60), height=340,
            annotations=[dict(text=f"€ {verb_tot['totaal']:,.0f}",
                              x=0.5, y=0.5, font_size=14, font_color="#1C1C2E",
                              showarrow=False, font=dict(weight="bold"))],
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Geen verbouwingsdata.")

# ── Inboedel donut ──────────────────────────────────────────────────────────
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
            showlegend=True, legend=dict(orientation="h", y=-0.25),
            margin=dict(l=0, r=0, t=0, b=60), height=340,
            annotations=[dict(text=f"€ {inbo_tot['totaal']:,.0f}",
                              x=0.5, y=0.5, font_size=14, font_color="#1C1C2E",
                              showarrow=False, font=dict(weight="bold"))],
        )
        st.plotly_chart(fig2, use_container_width=True)
    else:
        st.info("Geen inboedeldata.")

st.markdown("---")

# ══════════════════════════════════════════════════════════════════════════════
# SECTIE 4 – MAAND CASHFLOW CHART + VERMOGEN
# ══════════════════════════════════════════════════════════════════════════════
col_c, col_v = st.columns([3, 2])

with col_c:
    st.markdown("#### 📅 Maandbudget Verdeling")
    cats_maand = {
        "Wonen":      maand_tot.get("vaste", 0),
        "Variabel":   maand_tot.get("variabel", 0),
        "Sparen":     maand_tot.get("sparen", 0),
        "Buffer":     max(maand_tot.get("ruimte", 0), 0),
    }
    cats_maand = {k: v for k, v in cats_maand.items() if v > 0}
    if cats_maand:
        fig3 = go.Figure(go.Pie(
            labels=list(cats_maand.keys()),
            values=list(cats_maand.values()),
            hole=0.5,
            marker_colors=["#FF8C00", "#FFD700", "#10B981", "#3B82F6"],
            textinfo="label+value+percent",
            hovertemplate="<b>%{label}</b><br>€ %{value:,.0f} per maand<extra></extra>",
        ))
        fig3.update_layout(
            plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
            showlegend=False,
            margin=dict(l=0, r=0, t=0, b=0), height=280,
            annotations=[dict(text=f"€ {maand_tot.get('inkomen',0):,.0f}<br>/maand",
                              x=0.5, y=0.5, font_size=12, font_color="#1C1C2E",
                              showarrow=False)],
        )
        st.plotly_chart(fig3, use_container_width=True)

with col_v:
    st.markdown("#### 💎 Vermogen na Verbouwing")
    st.markdown("<br>", unsafe_allow_html=True)
    kpi("👤 Patrick",   f"€ {verm['patrick']:,.0f}",   "resterend vermogen", "blu")
    st.markdown("<br>", unsafe_allow_html=True)
    kpi("👤 Willianne", f"€ {verm['willianne']:,.0f}", "resterend vermogen", "grn")
    st.markdown("<br>", unsafe_allow_html=True)
    kpi("💎 Samen",     f"€ {verm['samen']:,.0f}",     "gezamenlijk vermogen")
    st.markdown("<br>", unsafe_allow_html=True)
    kpi("🏦 Nu gespaard", f"€ {verm['totaal_sparen']:,.0f}", "sparen + beleggen")

st.markdown("---")

# ══════════════════════════════════════════════════════════════════════════════
# SECTIE 5 – VERBOUWING BAR CHART (budget vs detail)
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
        margin=dict(l=0, r=80, t=10, b=0), height=280,
        font=dict(family="Inter"),
    )
    st.plotly_chart(fig4, use_container_width=True)

st.markdown("---")

# ══════════════════════════════════════════════════════════════════════════════
# SECTIE 6 – BEWERKBARE PROJECTINSTELLINGEN
# ══════════════════════════════════════════════════════════════════════════════
with st.expander("⚙️ Projectinstellingen aanpassen (Dashboard PRO)", expanded=False):
    st.caption("Wijzig onderstaande waarden. Klik 'Opslaan' om de berekeningen bij te werken.")
    dashboard_data = dash()
    df_dash = pd.DataFrame(
        [(k, v) for k, v in dashboard_data.items()],
        columns=["Instelling", "Waarde"],
    )
    edited = st.data_editor(
        df_dash,
        column_config={
            "Instelling": st.column_config.TextColumn("Instelling", width="large"),
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
                    new_d[k] = float(v)
                except (TypeError, ValueError):
                    new_d[k] = v
        set_dashboard(new_d)
        st.success("✅ Instellingen bijgewerkt — pagina herlaadt...")
        st.rerun()
