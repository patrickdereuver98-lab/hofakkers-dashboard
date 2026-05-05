"""
utils/ui.py  –  Hofakkers 44
Herbruikbare UI-componenten.

BUGS FIXED:
- kpi(): variant-mapping uitgebreid (blu/grn/red/success/warning/danger/neutral allemaal werkend)
- sidebar(): gebruikt correcte calc-functies en save_all_to_excel()
- CHART_COLORS: correct geïmporteerd als lijst (niet dict)
- progress(): variant-mapping gecorrigeerd
"""
import streamlit as st
from utils.config import CSS_STYLES, APP_CONFIG, CHART_COLORS


# ── Page setup ─────────────────────────────────────────────────────────────

def page_setup(title: str = "🏠 Hofakkers 44") -> None:
    st.set_page_config(
        page_title=title,
        page_icon=APP_CONFIG["icon"],
        layout=APP_CONFIG["layout"],
        initial_sidebar_state=APP_CONFIG["sidebar_state"],
    )
    inject_css()


def inject_css() -> None:
    st.markdown(CSS_STYLES, unsafe_allow_html=True)


# ── Header ─────────────────────────────────────────────────────────────────

def header(title: str, subtitle: str = "", emoji: str = "") -> None:
    emoji_html = f"<span style='font-size:2.2rem;margin-right:14px;'>{emoji}</span>" if emoji else ""
    sub_html   = f"<p style='color:rgba(26,26,46,.75);margin:4px 0 0;font-size:.95rem;'>{subtitle}</p>" if subtitle else ""
    st.markdown(f"""
    <div style='background:linear-gradient(100deg,#FFD700,#FF8C00);border-radius:20px;padding:22px 30px;margin-bottom:22px;box-shadow:0 12px 40px rgba(0,0,0,0.14);position:relative;overflow:hidden;'>
      <div style='display:flex;align-items:center;'>
        {emoji_html}
        <div>
          <h1 style='color:#1A1A2E;margin:0;font-size:1.9rem;font-weight:800;'>{title}</h1>
          {sub_html}
        </div>
      </div>
    </div>
    """, unsafe_allow_html=True)


# ── KPI Card ───────────────────────────────────────────────────────────────

def kpi(label: str, value: str, sub: str = "", variant: str = "") -> None:
    """
    Render een KPI-kaart.
    variant: '' | 'grn' | 'red' | 'blu' | 'success' | 'warning' | 'danger' | 'neutral'
    """
    # Normaliseer aliassen
    v_map = {
        "success": "grn", "danger": "red", "warning": "warning",
        "neutral": "", "blu": "blu", "grn": "grn", "red": "red",
    }
    cls = v_map.get(variant, "")
    sub_html = f'<div class="kpi-delta">{sub}</div>' if sub else ""
    st.markdown(f"""
    <div class="kpi-card {cls} animate-in">
      <div class="kpi-label">{label}</div>
      <div class="kpi-value">{value}</div>
      {sub_html}
    </div>
    """, unsafe_allow_html=True)


# ── Progress bar ───────────────────────────────────────────────────────────

def progress(label: str, pct: float, variant: str = "") -> None:
    """
    Render een voortgangsbalk.
    variant: '' | 'grn' | 'red'
    """
    p = min(max(float(pct), 0), 100)
    # Auto-kleur als geen variant opgegeven
    if not variant:
        cls = "red" if p > 90 else "grn" if p >= 70 else ""
    else:
        v_map = {"success": "grn", "danger": "red", "warning": "", "normal": ""}
        cls = v_map.get(variant, variant)

    st.markdown(f"""
    <div class="pgwrap">
      <div class="pglbl"><span>{label}</span><span>{p:.1f}%</span></div>
      <div class="pgbar"><div class="pgfill {cls}" style="width:{p}%;"></div></div>
    </div>
    """, unsafe_allow_html=True)


# ── Sidebar ────────────────────────────────────────────────────────────────

def sidebar(maand_totalen: dict = None, project_data: dict = None) -> None:
    """
    Globale sidebar met financiële KPI's, opslaan- en herlaadknoppen.
    """
    from utils.state import save_all_to_excel, reload

    mt = maand_totalen or {}
    pd = project_data  or {}

    with st.sidebar:
        st.markdown("""
        <div style='text-align:center;padding:10px 0 6px;'>
          <div style='font-size:2.8rem;'>🏠</div>
          <div style='font-size:1rem;font-weight:800;color:#FFD700;letter-spacing:.04em;'>HOFAKKERS 44</div>
          <div style='font-size:.68rem;color:#9CA3AF;letter-spacing:.12em;margin-top:2px;'>Patrick & Willianne</div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("---")

        # ── Project ──
        verb = pd.get("verbouwing", 0)
        inbo = pd.get("inboedel", 0)
        proj = pd.get("project",  0)
        st.markdown("#### 🏗️ Project Totaal")
        st.metric("Verbouwing",     f"€ {verb:,.0f}")
        st.metric("Inboedel",       f"€ {inbo:,.0f}")
        st.metric("Totaal project",  f"€ {proj:,.0f}")

        st.markdown("---")

        # ── Cashflow ──
        ink    = mt.get("inkomen", 0)
        uit    = mt.get("totaal_uitgaven", 0)
        ruimte = mt.get("ruimte", 0)
        st.markdown("#### 💳 Maand Cashflow")
        st.metric("Inkomen",  f"€ {ink:,.0f}")
        st.metric("Uitgaven", f"€ {uit:,.0f}")
        delta_kleur = "normal" if ruimte >= 0 else "inverse"
        st.metric("Buffer", f"€ {ruimte:,.0f}", delta_color=delta_kleur)

        if ink > 0:
            pct = min(uit / ink * 100, 100)
            bar_c = "#EF4444" if pct > 85 else "#F59E0B" if pct > 70 else "#10B981"
            st.markdown(f"""
            <div style='margin:2px 0 14px;'>
              <div style='background:rgba(255,255,255,.12);border-radius:999px;height:7px;'>
                <div style='width:{pct:.1f}%;height:100%;background:{bar_c};border-radius:999px;'></div>
              </div>
              <div style='font-size:.68rem;color:#9CA3AF;margin-top:3px;text-align:right;'>{pct:.0f}% van inkomen</div>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("---")

        # ── Vermogen ──
        st.markdown("#### 💎 Vermogen na verbouwing")
        st.metric("Patrick",   f"€ {pd.get('patrick',  0):,.0f}")
        st.metric("Willianne", f"€ {pd.get('willianne',0):,.0f}")
        st.metric("Samen",     f"€ {pd.get('samen',    0):,.0f}")

        st.markdown("---")

        # ── Acties ──
        if st.button("💾 Opslaan naar Excel", width='stretch', type="primary"):
            if save_all_to_excel():
                st.success("✅ Opgeslagen!")
            else:
                st.error("❌ Opslaan mislukt.")

        if st.button("🔄 Herladen uit Excel", width='stretch'):
            reload()
            st.rerun()

        st.markdown("---")
        st.caption("Hofakkers 44 · v2.1 · Bob de Bouwer SaaS")
