"""
ui/layout.py
Bevat de visuele schil, sidebar-logica en CSS-injecties.
"""
import streamlit as st
from config.config import CSS_STYLES, APP_CONFIG, COLORS

def inject_css():
    """Injecteert CSS stijlen in de app."""
    st.markdown(CSS_STYLES, unsafe_allow_html=True)

def setup_page_config():
    """Stelt de pagina configuratie in."""
    st.set_page_config(
        page_title=APP_CONFIG["title"],
        page_icon=APP_CONFIG["icon"],
        layout=APP_CONFIG["layout"],
        initial_sidebar_state=APP_CONFIG["sidebar_state"]
    )

def render_sidebar():
    """Rendert de sidebar met navigatie."""
    with st.sidebar:
        st.title("🏗️ Bouw Dashboard")
        st.markdown("---")
        
        # Metrics in sidebar
        if 'dashboard' in st.session_state:
            totaal_budget = st.session_state['dashboard'].get("Totaal Inleg Patrick", 0) + st.session_state['dashboard'].get("Totaal Inleg Willianne", 0)
            verbouwing = st.session_state.get('verbouwing', st.session_state.get('verbouwing', []))
            gerealiseerd = sum(row.get('Totaal (€)', 0) for row in verbouwing.itertuples() if hasattr(row, 'Totaal (€)')) if hasattr(verbouwing, 'itertuples') else 0
            beschikbaar = totaal_budget - gerealiseerd
            
            st.metric("💰 Totaal Budget", f"€ {totaal_budget:,.0f}")
            st.metric("✅ Besteed", f"€ {gerealiseerd:,.0f}", delta=f"€ {gerealiseerd:,.0f}")
            st.metric("🎯 Resterend", f"€ {beschikbaar:,.0f}", delta=f"€ {beschikbaar:,.0f}" if beschikbaar >= 0 else f"-€ {abs(beschikbaar):,.0f}", delta_color="inverse" if beschikbaar < 0 else "normal")
        
        st.markdown("---")
        st.caption("🚧 Bob de Bouwer Style 🚧")

def render_metric_card(title, value, delta=None, delta_color="normal"):
    """Rendert een gestylde metric card."""
    delta_html = f'<div style="color: {"green" if delta_color == "normal" else "red"}; font-size: 0.8em;">{delta}</div>' if delta else ""
    st.markdown(f"""
    <div class="metric-card">
        <h3>{title}</h3>
        <h2>{value}</h2>
        {delta_html}
    </div>
    """, unsafe_allow_html=True)

def render_tile(title, description, page_link, emoji):
    """Rendert een interactieve tegel voor de landingspagina."""
    st.markdown(f"""
    <div class="tile" onclick="window.location.href='{page_link}'">
        <h2>{emoji} {title}</h2>
        <p>{description}</p>
    </div>
    """, unsafe_allow_html=True)

def render_progress_bar(value, max_value, label=""):
    """Rendert een gestylde progress bar."""
    percentage = min((value / max_value) * 100, 100) if max_value > 0 else 0
    st.markdown(f"""
    <div style="margin: 10px 0;">
        <div style="display: flex; justify-content: space-between; margin-bottom: 5px;">
            <span>{label}</span>
            <span>{percentage:.1f}%</span>
        </div>
        <div class="progress-bar" style="width: 100%; background-color: #e0e0e0;">
            <div style="width: {percentage}%; height: 100%; background-color: {COLORS['primary']}; border-radius: 10px; transition: width 0.5s ease;"></div>
        </div>
    </div>
    """, unsafe_allow_html=True)