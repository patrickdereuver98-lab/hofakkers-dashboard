"""
pages/4_Vermogen.py  –  Hofakkers 44
Vermogensoverzicht Patrick & Willianne – aanpasbaar.
"""
import streamlit as st
import pandas as pd
import plotly.graph_objects as go

from utils.ui import page_setup, header, kpi, progress, sidebar
from utils.state import init, calc_maand_totalen, calc_project, calc_spaargeld, dash, set_dashboard
from utils.config import CHART_COLORS
from utils.excel_handler import save_dashboard

page_setup("💎 Vermogen – Hofakkers 44")
init()
sidebar(calc_maand_totalen(), calc_project())
header("💎 Vermogensoverzicht", "Patrick & Willianne · Na verbouwing Hofakkers 44")

proj = calc_project()
verm = calc_spaargeld()
d    = dash()

def sf(v):
    try: return float(v or 0)
    except: return 0.0

# ── KPI rij ─────────────────────────────────────────────────────────────────
c1, c2, c3, c4 = st.columns(4)
with c1: kpi("👤 Patrick",    f"€ {verm['patrick']:,.0f}",    "resterend vermogen", "blu")
with c2: kpi("👤 Willianne",  f"€ {verm['willianne']:,.0f}",  "resterend vermogen", "grn")
with c3: kpi("💎 Samen",      f"€ {verm['samen']:,.0f}",      "gezamenlijk")
with c4: kpi("🏦 Nu gespaard", f"€ {verm['totaal_sparen']:,.0f}", "sparen + beleggen")

st.markdown("---")

col_l, col_r = st.columns(2)

# ── Donut: vermogen verdeling ─────────────────────────────────────────────────
with col_l:
    st.markdown("##### 🍩 Vermogensverdeling na Verbouwing")
    fig = go.Figure(go.Pie(
        labels=["Patrick", "Willianne"],
        values=[max(verm["patrick"],0), max(verm["willianne"],0)],
        hole=0.55,
        marker_colors=["#3B82F6","#10B981"],
        textinfo="label+value+percent",
        hovertemplate="<b>%{label}</b><br>€ %{value:,.0f}<br>%{percent}<extra></extra>",
    ))
    fig.update_layout(
        plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
        showlegend=False, margin=dict(l=0,r=0,t=0,b=0), height=300,
        annotations=[dict(text=f"<b>€ {verm['samen']:,.0f}</b><br>samen",
                          x=0.5, y=0.5, font_size=12, showarrow=False)],
    )
    st.plotly_chart(fig, use_container_width=True)

# ── Waterval: project berekening ───────────────────────────────────────────────
with col_r:
    st.markdown("##### 📊 Project Kostenberekening")
    totaal_sparen_nu = verm["totaal_sparen"]
    projectkosten    = proj["project"]
    aankoopkosten    = sf(d.get("Benodigd geld woning (aankoopkosten + project)", 0)) - projectkosten
    resterend        = verm["samen"]

    fig2 = go.Figure(go.Waterfall(
        name="",
        orientation="v",
        measure=["absolute","relative","relative","total"],
        x=["💰 Huidig Vermogen","🔨 Verbouwing + Inboedel","🏠 Aankoopkosten","💎 Resterend"],
        y=[totaal_sparen_nu, -projectkosten, -max(aankoopkosten,0), 0],
        connector=dict(line=dict(color="#E5E7EB")),
        increasing=dict(marker_color="#10B981"),
        decreasing=dict(marker_color="#EF4444"),
        totals=dict(marker_color="#3B82F6"),
        text=[f"€{totaal_sparen_nu:,.0f}", f"-€{projectkosten:,.0f}",
              f"-€{max(aankoopkosten,0):,.0f}", f"€{resterend:,.0f}"],
        textposition="outside",
    ))
    fig2.update_layout(
        plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=0,r=0,t=10,b=0), height=300, showlegend=False,
        yaxis=dict(tickprefix="€"),
    )
    st.plotly_chart(fig2, use_container_width=True)

st.markdown("---")

# ── Aanpasbare vermogenswaarden ────────────────────────────────────────────────
st.markdown("##### ✏️ Vermogenswaarden aanpassen")
st.caption("Alle waarden komen rechtstreeks uit 'Dashboard PRO' in de Excel.")

verm_keys = [
    "Totaal sparen + beleggen nu",
    "Vermogen Patrick na verbouwing",
    "Vermogen Willianne na verbouwing",
    "Samen vermogen na verbouwing",
    "Verbouwing (totaal)",
    "Inboedel (totaal)",
    "Projectkosten samen (verbouwing + inboedel)",
    "Benodigd geld woning (aankoopkosten + project)",
    "Benodigd per persoon",
]

cols_ed = st.columns(3)
updated = dict(d)
for i, key in enumerate(verm_keys):
    if key in d:
        with cols_ed[i % 3]:
            new_v = st.number_input(
                key, value=sf(d.get(key, 0)), step=500.0, format="%.2f",
                key=f"verm_{key}",
            )
            updated[key] = new_v

if st.button("💾 Vermogenswaarden opslaan", type="primary"):
    set_dashboard(updated)
    if save_dashboard(updated):
        st.success("✅ Opgeslagen naar Excel!")
    else:
        st.success("✅ Bijgewerkt in app!")
    st.rerun()

st.markdown("---")

# ── Projectoverzicht tabel ─────────────────────────────────────────────────────
st.markdown("##### 📋 Volledig Projectoverzicht")
proj_data = [
    ("💰 Huidig gezamenlijk vermogen",      verm["totaal_sparen"]),
    ("🔨 Verbouwingskosten",                proj["verbouwing"]),
    ("🛋️ Inboedelkosten",                  proj["inboedel"]),
    ("📦 Totaal projectkosten",             proj["project"]),
    ("🏠 Aankoopkosten woning",             sf(d.get("Benodigd geld woning (aankoopkosten + project)",0)) - proj["project"]),
    ("👤 Benodigd per persoon",             proj["per_persoon"]),
    ("💎 Gezamenlijk resterend vermogen",   verm["samen"]),
    ("👤 Patrick resterend",                verm["patrick"]),
    ("👤 Willianne resterend",              verm["willianne"]),
]
df_proj = pd.DataFrame(proj_data, columns=["Omschrijving","Bedrag (€)"])
st.dataframe(
    df_proj.style.format({"Bedrag (€)": "€ {:,.0f}"})
                 .applymap(lambda x: "color: #10B981" if isinstance(x, (int,float)) and x > 0 else
                           ("color: #EF4444" if isinstance(x, (int,float)) and x < 0 else ""),
                           subset=["Bedrag (€)"]),
    use_container_width=True, hide_index=True,
)
