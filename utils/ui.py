"""
utils/ui.py
UI component adapter for new Bob de Bouwer dashboard pages.
Wraps layout.py + adds new component functions for interactive dashboards.
"""
import streamlit as st
from utils.config import APP_CONFIG, CSS_STYLES, COLORS, KAMER_EMOJIS


# ─────────────────────────────────────────────────────────────────────────
# PAGE SETUP
# ─────────────────────────────────────────────────────────────────────────

def page_setup(page_title: str) -> None:
    """
    Initialize page: config + CSS + session init.
    """
    st.set_page_config(
        page_title=page_title,
        page_icon=APP_CONFIG["icon"],
        layout="wide",
        initial_sidebar_state="expanded",
    )
    inject_css()


def inject_css() -> None:
    """Inject custom CSS styles for Bob de Bouwer theme."""
    st.markdown(CSS_STYLES, unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────────────
# HEADER COMPONENTS
# ─────────────────────────────────────────────────────────────────────────

def header(title: str, subtitle: str = "", emoji: str = "🏗️") -> None:
    """Render page header with emoji, title, subtitle."""
    st.markdown(f"""
    <div class="bdb-header animate-in">
      <div style='display:flex; align-items:center; gap:16px; margin-bottom:24px;'>
        <span style='font-size:2.5rem;'>{emoji}</span>
        <div>
          <h1 style='margin:0; color:#1A1A2E;'>{title}</h1>
          {f"<p style='margin:4px 0 0; color:#6B7280; font-size:0.95rem;'>{subtitle}</p>" if subtitle else ""}
        </div>
      </div>
    </div>
    """, unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────────────
# KPI CARD COMPONENT
# ─────────────────────────────────────────────────────────────────────────

def kpi(label: str, value: str, delta: str = "", variant: str = "neutral") -> None:
    """
    Render KPI card.
    variant: 'neutral' | 'success' | 'warning' | 'danger'
    """
    variant_colors = {
        "neutral": "#FFD700",
        "success": "#10B981",
        "warning": "#F59E0B",
        "danger": "#EF4444",
    }
    
    card_color = variant_colors.get(variant, "#FFD700")
    delta_html = ""
    if delta:
        delta_color = "#10B981" if "+" in delta else "#EF4444"
        delta_html = f"""
        <div style='font-size:0.75rem; color:{delta_color}; margin-top:4px; font-weight:600;'>
            {delta}
        </div>
        """
    
    st.markdown(f"""
    <div style='
        background:rgba(255,255,255,0.05);
        border:2px solid {card_color}33;
        border-radius:12px;
        padding:16px;
        text-align:center;
        margin-bottom:8px;
        transition:all 0.3s;
    '>
        <div style='font-size:0.85rem; color:#9CA3AF; text-transform:uppercase; letter-spacing:0.05em; margin-bottom:8px;'>
            {label}
        </div>
        <div style='font-size:2rem; font-weight:800; color:#1A1A2E;'>
            {value}
        </div>
        {delta_html}
    </div>
    """, unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────────────
# PROGRESS COMPONENT
# ─────────────────────────────────────────────────────────────────────────

def progress(label: str, percentage: float, variant: str = "normal") -> None:
    """
    Render progress bar.
    variant: 'normal' | 'success' | 'warning' | 'danger'
    """
    pct = min(max(percentage, 0), 100)
    
    variant_colors = {
        "normal": "#FFD700",
        "success": "#10B981",
        "warning": "#F59E0B",
        "danger": "#EF4444",
    }
    
    bar_color = variant_colors.get(variant, "#FFD700")
    
    st.markdown(f"""
    <div style='margin-bottom:16px;'>
        <div style='display:flex; justify-content:space-between; margin-bottom:6px;'>
            <span style='font-size:0.9rem; color:#1A1A2E; font-weight:600;'>{label}</span>
            <span style='font-size:0.85rem; color:#6B7280; font-weight:600;'>{pct:.1f}%</span>
        </div>
        <div style='background:rgba(0,0,0,0.1); border-radius:999px; height:10px; overflow:hidden;'>
            <div style='
                height:100%;
                width:{pct}%;
                background:{bar_color};
                border-radius:999px;
                transition:width 0.6s ease-out;
            '></div>
        </div>
    </div>
    """, unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────────────
# SIDEBAR COMPONENT
# ─────────────────────────────────────────────────────────────────────────

def sidebar(maand_totalen: dict = None, project_data: dict = None) -> None:
    """
    Render sidebar with financiële KPI's and project info.
    """
    with st.sidebar:
        # Header
        st.markdown("""
        <div style='text-align:center; padding:12px 0 8px; margin-bottom:16px;'>
            <div style='font-size:2.5rem;'>🏗️</div>
            <div style='font-size:1rem; font-weight:800; color:#FFD700; letter-spacing:0.04em;'>
                BOB DE BOUWER
            </div>
            <div style='font-size:0.65rem; color:#9CA3AF; letter-spacing:0.1em; margin-top:2px;'>
                RENOVATION SaaS
            </div>
        </div>
        """, unsafe_allow_html=True)

        st.divider()

        # Maand Totalen
        if maand_totalen:
            st.markdown("#### 💰 Cashflow")
            col1, col2 = st.columns(2)
            col1.metric("Inkomsten", f"€ {maand_totalen.get('inkomsten', 0):,.0f}")
            col2.metric("Uitgaven", f"€ {maand_totalen.get('uitgaven', 0):,.0f}")
            
            balance = maand_totalen.get('inkomsten', 0) - maand_totalen.get('uitgaven', 0)
            delta_color = "normal" if balance >= 0 else "inverse"
            st.metric(
                "Saldo",
                f"€ {balance:,.0f}",
                delta_color=delta_color
            )
            st.divider()

        # Project Data
        if project_data:
            st.markdown("#### 🏠 Project")
            st.metric("Budget", f"€ {project_data.get('budget', 0):,.0f}")
            st.metric("Besteed", f"€ {project_data.get('besteed', 0):,.0f}")
            
            remaining = project_data.get('budget', 0) - project_data.get('besteed', 0)
            pct_used = (project_data.get('besteed', 0) / max(project_data.get('budget', 1), 1)) * 100
            
            delta_color = "normal" if remaining >= 0 else "inverse"
            st.metric(
                "Resterend",
                f"€ {remaining:,.0f}",
                delta=f"{pct_used:.1f}% gebruikt",
                delta_color=delta_color
            )
            st.divider()

        # Contributers
        dashboard = st.session_state.get("dashboard", {})
        pat = float(dashboard.get("Totaal Inleg Patrick", 0) or 0)
        wil = float(dashboard.get("Totaal Inleg Willianne", 0) or 0)
        
        st.markdown("#### 👥 Bijdragers")
        col1, col2 = st.columns(2)
        col1.metric("Patrick", f"€ {pat:,.0f}")
        col2.metric("Willianne", f"€ {wil:,.0f}")
        
        st.divider()
        st.caption("Hofakkers 44 · Bob de Bouwer SaaS · v2.0")


# ─────────────────────────────────────────────────────────────────────────
# CHART COLORS
# ─────────────────────────────────────────────────────────────────────────

CHART_COLORS = COLORS.get("chart", {
    "geel": "#FFD700",
    "oranje": "#FF8C00",
    "groen": "#10B981",
    "rood": "#EF4444",
    "antraciet": "#1A1A2E",
})
