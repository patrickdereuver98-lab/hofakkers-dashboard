"""
app.py
Centrale landingspagina voor het Hofakkers 44 Renovatie Dashboard.
"""
import streamlit as st
import pandas as pd
import plotly.express as px
from utils.layout import setup_page_config, inject_css, render_sidebar, render_tile_card, render_metric_card, render_progress_card
from utils.state_manager import init_session_state, get_dashboard_dataframe, save_dashboard_dataframe, get_budget_data, save_budget_data, get_rooms, save_session_state_to_excel
from utils.calculations import calculate_totals, calculate_budget_distribution, calculate_user_shares, calculate_overall_progress

setup_page_config()
inject_css()
init_session_state()
render_sidebar()

st.title("🏠 Hofakkers 44 Renovatie Dashboard")
st.markdown("**Live Excel-powered SAAS in Bob de Bouwer stijl. Klik op een tegel om te navigeren.**")

st.markdown("---")

# Landingspagina tegels
col1, col2 = st.columns(2)
with col1:
    render_tile_card("Hoofddashboard", "Realtime financiële overzichten, voortgang en kamerstatistieken.", "pages/1_Hoofddashboard.py", "📊")
    render_tile_card("Kamer Slaapkamer", "Direct naar de slaapkamer planning, budget en taken.", "pages/kamer_slaapkamer.py", "🛏️")
with col2:
    render_tile_card("Kamer Keuken", "Bekijk kosten, taken en wensen voor de keuken.", "pages/kamer_keuken.py", "🍳")
    render_tile_card("Kamer Badkamer", "Beheer renovatiebudget en taken per badkamer.", "pages/kamer_badkamer.py", "🛁")

st.markdown("---")

# Dashboard data editor
st.subheader("👥 Gebruikers & Inleg")
dashboard_df = get_dashboard_dataframe()
edited_dashboard = st.data_editor(
    dashboard_df,
    column_config={
        'Sleutel': st.column_config.TextColumn('Sleutel', width='small'),
        'Waarde': st.column_config.NumberColumn('Waarde', format='€ %.2f')
    },
    num_rows='dynamic',
    use_container_width=True,
)

if st.button("💾 Sla basisgegevens op"):
    save_dashboard_dataframe(edited_dashboard)
    st.success("Dashboard gegevens bijgewerkt in session state.")

st.markdown("---")

summary = calculate_totals()
shares = calculate_user_shares()

col1, col2, col3, col4 = st.columns(4)
with col1:
    render_metric_card("Totaal Budget", f"€ {summary['totaal_budget']:,.0f}")
with col2:
    render_metric_card("Besteed", f"€ {summary['besteed']:,.0f}")
with col3:
    render_metric_card("Resterend", f"€ {summary['beschikbaar']:,.0f}")
with col4:
    render_metric_card("Voortgang totaal", f"{summary['percentage']:.1f}%")

st.markdown("---")

st.subheader("💰 Verdeling per persoon")
col1, col2 = st.columns(2)
with col1:
    st.metric("Patrick", f"€ {shares['Patrick']['value']:,.0f}", delta=f"{shares['Patrick']['percentage']:.1f}%")
with col2:
    st.metric("Willianne", f"€ {shares['Willianne']['value']:,.0f}", delta=f"{shares['Willianne']['percentage']:.1f}%")

st.markdown("---")

st.subheader("🏠 Kameroverzicht")
budget_dist = calculate_budget_distribution()
if budget_dist:
    room_df = pd.DataFrame(budget_dist)
    fig = px.pie(room_df, names='kamer', values='budget', title='Budgetverdeling per kamer', hole=0.4)
    fig.update_traces(marker=dict(colors=['#FFD700', '#FF8C00', '#FFA500', '#FFB347', '#FFDA79']))
    st.plotly_chart(fig, use_container_width=True)

    for room_summary in budget_dist:
        col1, col2, col3 = st.columns(3)
        with col1:
            st.markdown(f"**{room_summary['kamer']}**")
        with col2:
            st.write(f"Budget: € {room_summary['budget']:,.0f}")
        with col3:
            st.write(f"Resterend: € {room_summary['remaining']:,.0f}")
else:
    st.info("Nog geen budgetverdeling aanwezig. Ga naar een kamerpagina om budgetten toe te voegen.")

st.markdown("---")

st.subheader("📈 Woning voortgang")
progress = calculate_overall_progress()
render_progress_card("Gemiddelde kamer voortgang", progress)

st.markdown("---")
if st.button("💾 Opslaan naar Excel"):
    if save_session_state_to_excel():
        st.success("✅ Alles succesvol naar Excel weggeschreven.")
    else:
        st.error("❌ Opslaan naar Excel mislukt.")
