"""
utils/layout.py
Visuele hub: page config, CSS, sidebar, gedeelde UI-componenten.
Bob de Bouwer SaaS – Interactief, Geel, Slick.
"""
import streamlit as st
from utils.config import APP_CONFIG, CSS_STYLES, KAMER_EMOJIS, COLORS


# ── Page config ────────────────────────────────────────────────────────────

def setup_page_config() -> None:
    st.set_page_config(
        page_title=APP_CONFIG["title"],
        page_icon=APP_CONFIG["icon"],
        layout=APP_CONFIG["layout"],
        initial_sidebar_state=APP_CONFIG["sidebar_state"],
    )


def inject_css() -> None:
    st.markdown(CSS_STYLES, unsafe_allow_html=True)


# ── Sidebar ────────────────────────────────────────────────────────────────

def render_sidebar() -> None:
    from utils.calculations import calculate_totals, calculate_overall_progress
    from utils.state_manager import save_to_excel, reload_from_excel

    totals   = calculate_totals()
    progress = calculate_overall_progress()

    with st.sidebar:
        st.markdown("""
        <div style='text-align:center; padding: 12px 0 8px;'>
          <div style='font-size:3rem;'>🏗️</div>
          <div style='font-size:1.2rem; font-weight:800; color:#FFD700; letter-spacing:0.04em;'>BOB DE BOUWER</div>
          <div style='font-size:0.75rem; color:#9CA3AF; letter-spacing:0.1em;'>RENOVATION SaaS</div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("---")

        # Financiële KPI's
        st.markdown("#### 💰 Financieel Overzicht")
        st.metric("Totaal Budget",  f"€ {totals['totaal_budget']:,.0f}")
        st.metric("Besteed",        f"€ {totals['besteed']:,.0f}")
        delta_kleur = "normal" if totals["beschikbaar"] >= 0 else "inverse"
        st.metric("Resterend",
                  f"€ {totals['beschikbaar']:,.0f}",
                  delta=f"{totals['percentage']:.1f}% gebruikt",
                  delta_color=delta_kleur)

        # Voortgangsbalk
        pct = min(max(totals["percentage"] / 100, 0.0), 1.0)
        bar_color = "#EF4444" if pct > 0.9 else "#F59E0B" if pct > 0.7 else "#FFD700"
        st.markdown(f"""
        <div style='margin: 8px 0 16px;'>
          <div style='display:flex; justify-content:space-between; font-size:0.75rem; color:#9CA3AF; margin-bottom:4px;'>
            <span>Budget voortgang</span><span>{totals['percentage']:.1f}%</span>
          </div>
          <div style='background:rgba(255,255,255,0.1); border-radius:999px; height:8px; overflow:hidden;'>
            <div style='height:100%; width:{min(totals["percentage"],100):.1f}%; background:{bar_color}; border-radius:999px; transition:width 0.6s;'></div>
          </div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("---")

        # Taakoverzicht
        st.markdown(f"#### ✅ Voortgang Taken")
        st.markdown(f"""
        <div style='font-size:1.8rem; font-weight:800; color:#FFD700; text-align:center; margin-bottom:4px;'>{progress:.0f}%</div>
        <div style='background:rgba(255,255,255,0.1); border-radius:999px; height:8px; margin-bottom:12px;'>
          <div style='height:100%; width:{progress:.1f}%; background:#10B981; border-radius:999px;'></div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("---")

        # Bijdragers
        dashboard = st.session_state.get("dashboard", {})
        pat = float(dashboard.get("Totaal Inleg Patrick", 0) or 0)
        wil = float(dashboard.get("Totaal Inleg Willianne", 0) or 0)
        st.markdown("#### 👥 Bijdragers")
        col1, col2 = st.columns(2)
        col1.metric("Patrick",   f"€ {pat:,.0f}")
        col2.metric("Willianne", f"€ {wil:,.0f}")

        st.markdown("---")

        # Acties
        st.markdown("#### ⚡ Acties")
        if st.button("💾 Opslaan naar Excel", use_container_width=True):
            if save_to_excel():
                st.success("✅ Opgeslagen!")
            else:
                st.error("❌ Opslaan mislukt.")

        if st.button("🔄 Herladen uit Excel", use_container_width=True):
            reload_from_excel()
            st.rerun()

        st.markdown("---")
        st.caption("Hofakkers 44 · Bob de Bouwer SaaS · v2.0")


# ── Header banner ──────────────────────────────────────────────────────────

def render_header(title: str, subtitle: str = "", emoji: str = "🏗️") -> None:
    st.markdown(f"""
    <div class="bdb-header animate-in">
      <div style='display:flex; align-items:center; gap:16px;'>
        <span style='font-size:3rem;'>{emoji}</span>
        <div>
          <h1>{title}</h1>
          <p>{subtitle}</p>
        </div>
      </div>
    </div>
    """, unsafe_allow_html=True)


# ── KPI Card ───────────────────────────────────────────────────────────────

def render_kpi(label: str, value: str, delta: str = "", variant: str = "") -> None:
    """
    variant: '' | 'success' | 'warning' | 'danger'
    """
    delta_html = f"<div class='kpi-delta'>{delta}</div>" if delta else ""
    st.markdown(f"""
    <div class="kpi-card {variant} animate-in">
      <div class="kpi-label">{label}</div>
      <div class="kpi-value">{value}</div>
      {delta_html}
    </div>
    """, unsafe_allow_html=True)


# ── Voortgangsbalk ─────────────────────────────────────────────────────────

def render_progress(label: str, percentage: float, show_pct: bool = True) -> None:
    pct = min(max(percentage, 0), 100)
    cls = "danger" if pct > 95 else "success" if pct >= 80 else ""
    pct_label = f"{pct:.1f}%" if show_pct else ""
    st.markdown(f"""
    <div style='margin-bottom:12px;'>
      <div class='progress-label'><span>{label}</span><span>{pct_label}</span></div>
      <div class='progress-wrap'><div class='progress-fill {cls}' style='width:{pct}%;'></div></div>
    </div>
    """, unsafe_allow_html=True)


# ── Navigatietegel ─────────────────────────────────────────────────────────

def render_tegel(kamer: str, summary: dict) -> None:
    """Grote klikbare tegel voor een kamer op de landingspagina."""
    emoji   = KAMER_EMOJIS.get(kamer, "🏗️")
    budget  = summary.get("toegewezen", 0)
    besteed = summary.get("besteed", 0)
    rest    = summary.get("beschikbaar", 0)
    pct     = summary.get("pct_budget", 0)
    n_taken = summary.get("n_taken", 0)
    n_gereed = summary.get("n_gereed", 0)

    rest_kleur = "#EF4444" if rest < 0 else "#10B981"
    rest_str   = f"<span style='color:{rest_kleur}'>€ {rest:,.0f}</span>"

    pct_bar = min(pct, 100)
    bar_col = "#EF4444" if pct > 100 else "#F59E0B" if pct > 80 else "#10B981"

    st.markdown(f"""
    <div class="tegel-card animate-in">
      <span class="tegel-emoji">{emoji}</span>
      <h3>{kamer}</h3>
      <div style='font-size:0.82rem; color:#6B7280;'>{n_gereed}/{n_taken} taken gereed</div>
      <div style='margin:10px 0 6px;'>
        <div style='background:#F3F4F6; border-radius:999px; height:6px;'>
          <div style='width:{pct_bar:.1f}%; height:100%; background:{bar_col}; border-radius:999px;'></div>
        </div>
      </div>
      <div class="tegel-budget">
        🎯 Budget: € {budget:,.0f} &nbsp;|&nbsp; ✅ Besteed: € {besteed:,.0f} &nbsp;|&nbsp; 💰 Rest: {rest_str}
      </div>
    </div>
    """, unsafe_allow_html=True)


# ── Section box ────────────────────────────────────────────────────────────

def render_section(title: str, content_fn) -> None:
    st.markdown(f'<div class="section-box">', unsafe_allow_html=True)
    st.markdown(f"##### {title}")
    content_fn()
    st.markdown("</div>", unsafe_allow_html=True)


# ── Status badge ───────────────────────────────────────────────────────────

def status_badge(status: str) -> str:
    mapping = {
        "Todo":          "badge-todo",
        "Bezig":         "badge-bezig",
        "Gereed":        "badge-gereed",
        "Idee":          "badge-idee",
        "Gepland":       "badge-gepland",
        "Gerealiseerd":  "badge-gerealiseerd",
    }
    cls = mapping.get(status, "badge-todo")
    return f'<span class="badge {cls}">{status}</span>'


# ── Alert helpers ──────────────────────────────────────────────────────────

def alert_success(msg: str) -> None:
    st.markdown(f'<div class="alert-success">✅ {msg}</div>', unsafe_allow_html=True)


def alert_warning(msg: str) -> None:
    st.markdown(f'<div class="alert-warning">⚠️ {msg}</div>', unsafe_allow_html=True)


def alert_error(msg: str) -> None:
    st.markdown(f'<div class="alert-error">❌ {msg}</div>', unsafe_allow_html=True)


# ── Kamer page bootstrap ───────────────────────────────────────────────────

def kamer_page_setup(kamer: str) -> None:
    """Standaard initialisatie voor iedere kamerpagina."""
    from utils.state_manager import init_session_state
    setup_page_config()
    inject_css()
    init_session_state()
    render_sidebar()
    emoji = KAMER_EMOJIS.get(kamer, "🏗️")
    render_header(kamer, f"Renovatie overzicht voor de {kamer.lower()}", emoji)
