"""
app.py – Hofakkers 44 Renovatie Dashboard
Bob de Bouwer SaaS · Visuele Hub · Interactief
"""
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from utils.layout import setup_page_config, inject_css, render_sidebar, render_header, render_kpi, render_progress, render_tegel
from utils.state_manager import init_session_state, save_dashboard_df, get_dashboard_df, save_to_excel, get_budget_df, save_budget_df
from utils.calculations import calculate_totals, calculate_budget_distribution, calculate_user_shares, calculate_overall_progress, calculate_all_rooms, calculate_kosten_per_categorie
from utils.config import PLOTLY_COLORS, KAMER_EMOJIS

# ── Basis setup ─────────────────────────────────────────────────────────────
setup_page_config()
inject_css()
init_session_state()
render_sidebar()

# ── Header ──────────────────────────────────────────────────────────────────
render_header(
    "Hofakkers 44 – Renovatie Dashboard",
    "Realtime budgetbeheer · Bob de Bouwer SaaS · Volledig bewerkbaar",
    "🏗️",
)

# ── Financiële KPI's ────────────────────────────────────────────────────────
totals = calculate_totals()
shares = calculate_user_shares()
progress_pct = calculate_overall_progress()

c1, c2, c3, c4, c5 = st.columns(5)
with c1:
    render_kpi("💰 Totaal Budget",  f"€ {totals['totaal_budget']:,.0f}")
with c2:
    render_kpi("🔨 Besteed",        f"€ {totals['besteed']:,.0f}",
               delta=f"{totals['percentage']:.1f}%",
               variant="warning" if totals["percentage"] > 70 else "")
with c3:
    variant = "danger" if totals["beschikbaar"] < 0 else "success"
    render_kpi("🎯 Resterend",      f"€ {totals['beschikbaar']:,.0f}", variant=variant)
with c4:
    render_kpi("👤 Patrick",        f"€ {shares['Patrick']['value']:,.0f}",
               delta=f"{shares['Patrick']['pct']:.0f}%")
with c5:
    render_kpi("👤 Willianne",      f"€ {shares['Willianne']['value']:,.0f}",
               delta=f"{shares['Willianne']['pct']:.0f}%")

st.markdown("<br>", unsafe_allow_html=True)

# ── Voortgangsbalk totaal ───────────────────────────────────────────────────
render_progress("📈 Algehele Budget-uitputting", totals["percentage"])
render_progress("✅ Gemiddelde Taken Voortgang",  progress_pct)

st.markdown("---")

# ── Charts ──────────────────────────────────────────────────────────────────
col_chart1, col_chart2 = st.columns([3, 2])

with col_chart1:
    st.subheader("🏠 Budget per Kamer")
    budget_dist = calculate_budget_distribution()
    if budget_dist:
        df_bud = pd.DataFrame(budget_dist)
        fig = go.Figure()
        fig.add_trace(go.Bar(
            name="Toegewezen",
            x=df_bud["kamer"],
            y=df_bud["budget"],
            marker_color=PLOTLY_COLORS[0],
            text=df_bud["budget"].apply(lambda x: f"€{x:,.0f}"),
            textposition="auto",
        ))
        fig.add_trace(go.Bar(
            name="Besteed",
            x=df_bud["kamer"],
            y=df_bud["besteed"],
            marker_color=PLOTLY_COLORS[1],
            text=df_bud["besteed"].apply(lambda x: f"€{x:,.0f}"),
            textposition="auto",
        ))
        fig.update_layout(
            barmode="group",
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
            font=dict(family="Inter", size=12),
            legend=dict(orientation="h", y=-0.2),
            margin=dict(l=0, r=0, t=20, b=0),
            height=320,
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Geen budgetdata aanwezig.")

with col_chart2:
    st.subheader("🍩 Verdeling Kosten")
    kosten_cat = calculate_kosten_per_categorie()
    if kosten_cat:
        fig2 = go.Figure(go.Pie(
            labels=list(kosten_cat.keys()),
            values=list(kosten_cat.values()),
            hole=0.55,
            marker_colors=PLOTLY_COLORS,
            textinfo="label+percent",
        ))
        fig2.update_layout(
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
            showlegend=False,
            margin=dict(l=0, r=0, t=20, b=0),
            height=320,
        )
        st.plotly_chart(fig2, use_container_width=True)
    else:
        st.info("Nog geen kosten geregistreerd.")

st.markdown("---")

# ── Kamer tegels ────────────────────────────────────────────────────────────
st.subheader("🏡 Kamer Overzicht – klik op een pagina in de zijbalk")
all_rooms = calculate_all_rooms()

cols = st.columns(3)
for i, summary in enumerate(all_rooms):
    with cols[i % 3]:
        render_tegel(summary["kamer"], summary)

st.markdown("---")

# ── Bewerkbare instellingen ─────────────────────────────────────────────────
with st.expander("⚙️ Projectinstellingen & Inleg bewerken", expanded=False):
    st.markdown("Wijzigingen worden direct doorgerekend naar het hele dashboard.")
    dash_df = get_dashboard_df()
    edited_dash = st.data_editor(
        dash_df,
        column_config={
            "Sleutel": st.column_config.TextColumn("Sleutel", width="medium"),
            "Waarde":  st.column_config.TextColumn("Waarde", width="medium"),
        },
        num_rows="dynamic",
        use_container_width=True,
        key="editor_dashboard",
    )
    if st.button("💾 Projectinstellingen opslaan", type="primary"):
        save_dashboard_df(edited_dash)
        st.success("✅ Instellingen bijgewerkt!")
        st.rerun()

with st.expander("📊 Budget Verdeling per Kamer bewerken", expanded=False):
    st.markdown("Pas de toegewezen budgetten per kamer aan. Wijzigingen worden realtime doorgerekend.")
    bud_df = get_budget_df()
    edited_bud = st.data_editor(
        bud_df,
        column_config={
            "Kamer":                   st.column_config.TextColumn("Kamer", disabled=True),
            "Toegewezen Budget (€)":   st.column_config.NumberColumn("Toegewezen Budget", format="€ %.2f", min_value=0),
            "Gerealiseerd (€)":        st.column_config.NumberColumn("Gerealiseerd", format="€ %.2f", min_value=0),
            "Beschikbaar (€)":         st.column_config.NumberColumn("Beschikbaar", format="€ %.2f"),
        },
        num_rows="fixed",
        use_container_width=True,
        key="editor_budget",
    )
    if st.button("💾 Budgetten opslaan", type="primary"):
        save_budget_df(edited_bud)
        st.success("✅ Budgetten bijgewerkt!")
        st.rerun()

st.markdown("---")

# ── Verbouwing begroting totaaloverzicht ─────────────────────────────────────
with st.expander("🧾 Volledige Verbouwing Begroting (readonly overzicht)", expanded=False):
    verb = st.session_state.get("verbouwing", pd.DataFrame())
    if not verb.empty:
        st.dataframe(verb, use_container_width=True, height=400)
        totaal_verb = float(verb["Totaal (€)"].sum()) if "Totaal (€)" in verb.columns else 0
        st.metric("Totaal verbouwingsbegroting", f"€ {totaal_verb:,.2f}")
    else:
        st.info("Geen verbouwingsbegroting geladen.")

# ── Global save ──────────────────────────────────────────────────────────────
st.markdown("---")
col_save, col_spacer = st.columns([2, 5])
with col_save:
    if st.button("💾 Alles opslaan naar Excel", type="primary", use_container_width=True):
        if save_to_excel():
            st.success("✅ Volledig opgeslagen naar Excel!")
        else:
            st.error("❌ Opslaan mislukt.")
