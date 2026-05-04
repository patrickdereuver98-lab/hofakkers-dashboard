import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from ui.layout import render_sidebar, render_metric_card, inject_css
from utils.calculations import calculate_totals, calculate_budget_per_kamer
from config.config import PLOTLY_CONFIG

# Setup
inject_css()
render_sidebar()

st.title("📊 Hoofddashboard - Budgetoverzicht")

# Berekeningen
totals = calculate_totals()
kamer_budgetten = calculate_budget_per_kamer()

# Metrics
col1, col2, col3 = st.columns(3)
with col1:
    render_metric_card("💰 Totaal Budget", f"€ {totals['totaal_budget']:,.0f}")
with col2:
    render_metric_card("✅ Besteed", f"€ {totals['gerealiseerd']:,.0f}", delta=f"€ {totals['gerealiseerd']:,.0f}")
with col3:
    delta_color = "normal" if totals['beschikbaar'] >= 0 else "inverse"
    render_metric_card("🎯 Resterend", f"€ {totals['beschikbaar']:,.0f}", delta=f"€ {totals['beschikbaar']:,.0f}", delta_color=delta_color)

st.markdown("---")

# Plotly Donut Diagram voor budgetverdeling per kamer
if kamer_budgetten:
    labels = [k['kamer'] for k in kamer_budgetten]
    values = [k['budget'] for k in kamer_budgetten]
    
    fig = go.Figure(data=[go.Pie(
        labels=labels,
        values=values,
        hole=.4,
        marker_colors=['#FFD700', '#FF8C00', '#FFA500', '#FF6347', '#32CD32']
    )])
    
    fig.update_layout(
        title="Budgetverdeling per Kamer",
        font=dict(size=14),
        showlegend=True,
        **PLOTLY_CONFIG
    )
    
    st.plotly_chart(fig, use_container_width=True)
else:
    st.info("Geen budgetverdeling ingesteld. Ga naar Budget Verdeling om enveloppen per kamer in te stellen.")

# Detail tabel
st.subheader("📋 Budget Details per Kamer")
if kamer_budgetten:
    df = pd.DataFrame(kamer_budgetten)
    df.columns = ['Kamer', 'Budget (€)', 'Besteed (€)', 'Resterend (€)']
    st.dataframe(df, use_container_width=True)
else:
    st.write("Geen data beschikbaar.")

st.markdown("---")
st.subheader("🏠 Kamer Overzicht")

if kamer_budgetten:
    cols = st.columns(4)
    for i, kamer in enumerate(kamer_budgetten[:4]):  # Toon eerste 4 kamers
        with cols[i % 4]:
            from ui.components import render_card
            content = f"""
            Budget: € {kamer['budget']:,.0f}<br>
            Besteed: € {kamer['besteed']:,.0f}<br>
            Resterend: € {kamer['resterend']:,.0f}
            """
            render_card(kamer['kamer'], content, "🏠")

st.markdown("---")
st.subheader("📈 Voortgang")

# Simpele voortgang berekening
totaal_budget = totals['totaal_budget']
besteed = totals['gerealiseerd']
voortgang = (besteed / totaal_budget * 100) if totaal_budget > 0 else 0

from ui.components import render_progress_bar
render_progress_bar(voortgang, 100, "Algemene Voortgang")

st.markdown("---")
st.subheader("✅ Taken Status")

# Simpele taken telling (dit zou uitgebreid kunnen worden)
st.info("Taken per kamer kunnen worden bekeken op de individuele kamer pagina's.")