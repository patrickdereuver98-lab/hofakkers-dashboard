"""
utils/layout.py
Visuele styling, page config en terugkerende UI-componenten.
"""
import streamlit as st
from utils.config import APP_CONFIG, COLORS, CSS_STYLES
from utils.calculations import calculate_totals


def setup_page_config():
    st.set_page_config(
        page_title=APP_CONFIG['title'],
        page_icon=APP_CONFIG['icon'],
        layout=APP_CONFIG['layout'],
        initial_sidebar_state=APP_CONFIG['sidebar_state'],
    )


def inject_css():
    st.markdown(CSS_STYLES, unsafe_allow_html=True)


def render_sidebar():
    totals = calculate_totals()
    with st.sidebar:
        st.markdown("# 🏗️ Bob de Bouwer SaaS")
        st.markdown("---")
        st.metric("💰 Totaal Budget", f"€ {totals['totaal_budget']:,.0f}")
        st.metric("✅ Besteed", f"€ {totals['besteed']:,.0f}")
        st.metric("🎯 Resterend", f"€ {totals['beschikbaar']:,.0f}")
        st.progress(min(max(totals['percentage'] / 100, 0.0), 1.0))
        st.markdown("---")
        st.write("**Quick links**")
        st.markdown("- Landingspagina\n- Hoofddashboard\n- Kamer overzicht")
        st.markdown("---")
        st.caption("Bob de Bouwer SaaS - Interactief renovatieplatform")


def render_tile_card(title, description, target, emoji="🏗️"):
    st.markdown(f"""
    <a href="{target}" class="tile-card" style="display: block; color: inherit;">
      <h3>{emoji} {title}</h3>
      <p>{description}</p>
    </a>
    """, unsafe_allow_html=True)


def render_metric_card(title, value, delta=None):
    delta_html = f"<span style='font-size:0.9rem; color:#444444;'>+{delta}</span>" if delta else ""
    st.markdown(f"""
    <div class="metric-card">
      <h3>{title}</h3>
      <h2>{value}</h2>
      {delta_html}
    </div>
    """, unsafe_allow_html=True)


def render_progress_card(label, percentage):
    st.markdown(f"""
    <div class="progress-card">
      <div style="display:flex; justify-content: space-between; align-items: center; margin-bottom: 12px;">
        <strong>{label}</strong><span>{percentage:.1f}%</span>
      </div>
      <div class="progress-bar"><div class="progress-bar-inner" style="width: {percentage:.1f}%;"></div></div>
    </div>
    """, unsafe_allow_html=True)
