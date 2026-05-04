import streamlit as st
import pandas as pd
from ui.layout import render_sidebar, render_metric_card, inject_css
from utils.calculations import calculate_totals, validate_budget_consistency

# Setup
inject_css()
render_sidebar()

st.title("💰 Budget Verdeling")

st.markdown("Verdeel het totale budget in enveloppen per kamer. Dit helpt bij het beheren van uitgaven per ruimte.")

# Haal totaal budget
totals = calculate_totals()
totaal_budget = totals['totaal_budget']

st.metric("💰 Totaal Budget", f"€ {totaal_budget:,.0f}")

# Haal huidige budget verdeling
budget_df = st.session_state.get('budget_verdeling', pd.DataFrame(columns=['Kamer', 'Toegewezen Budget (€)', 'Gerealiseerd (€)', 'Beschikbaar (€)']))

# Data editor voor budget verdeling
edited_df = st.data_editor(
    budget_df,
    column_config={
        "Kamer": st.column_config.TextColumn("Kamer", width="medium"),
        "Toegewezen Budget (€)": st.column_config.NumberColumn("Toegewezen Budget (€)", min_value=0.0, step=0.01, format="€ %.2f"),
        "Gerealiseerd (€)": st.column_config.NumberColumn("Gerealiseerd (€)", min_value=0.0, step=0.01, format="€ %.2f", disabled=True),
        "Beschikbaar (€)": st.column_config.NumberColumn("Beschikbaar (€)", min_value=0.0, step=0.01, format="€ %.2f", disabled=True),
    },
    num_rows="dynamic",
    use_container_width=True
)

# Bereken beschikbare bedragen
for idx, row in edited_df.iterrows():
    toegewezen = row.get('Toegewezen Budget (€)', 0)
    gerealiseerd = row.get('Gerealiseerd (€)', 0)
    edited_df.at[idx, 'Beschikbaar (€)'] = toegewezen - gerealiseerd

# Validatie
validation = validate_budget_consistency()
totaal_toegewezen = validation['totaal_toegewezen']
verschil = validation['verschil']

col1, col2 = st.columns(2)
with col1:
    render_metric_card("📊 Totaal Toegewezen", f"€ {totaal_toegewezen:,.0f}")
with col2:
    color = "normal" if verschil >= 0 else "inverse"
    render_metric_card("⚖️ Verschil", f"€ {verschil:,.0f}", delta=f"€ {verschil:,.0f}", delta_color=color)

if not validation['consistent']:
    if verschil > 0:
        st.warning(f"Er is € {verschil:,.0f} budget niet toegewezen.")
    else:
        st.error(f"Budget overschrijding van € {abs(verschil):,.0f}!")

# Opslaan
if st.button("💾 Opslaan Budget Verdeling", type="primary"):
    st.session_state['budget_verdeling'] = edited_df
    st.success("✅ Budget verdeling opgeslagen!")
    st.rerun()