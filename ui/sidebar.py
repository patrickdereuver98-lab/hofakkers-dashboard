"""
ui/sidebar.py
Sidebar componenten.
"""
import streamlit as st
from utils.calculations import calculate_totals
from config.config import COLORS

def render_sidebar():
    """Rendert de sidebar met navigatie en metrics."""
    with st.sidebar:
        st.title("🏗️ Woning Dashboard")
        st.markdown("---")
        
        # Metrics in sidebar
        totals = calculate_totals()
        
        st.metric("💰 Totaal Budget", f"€ {totals['totaal_budget']:,.0f}")
        st.metric("✅ Besteed", f"€ {totals['gerealiseerd']:,.0f}", delta=f"€ {totals['gerealiseerd']:,.0f}")
        st.metric("🎯 Resterend", f"€ {totals['beschikbaar']:,.0f}", delta=f"€ {totals['beschikbaar']:,.0f}" if totals['beschikbaar'] >= 0 else f"-€ {abs(totals['beschikbaar']):,.0f}", delta_color="inverse" if totals['beschikbaar'] < 0 else "normal")
        
        st.markdown("---")
        st.caption("🏠 Hofakkers 44")