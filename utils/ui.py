"""
utils/ui.py  –  Hofakkers 44  v3.0

NIEUW v3:
- hero_kpi():        grote hero KPI met emoji, voor "in één oogopslag" overzicht
- stat_strip():      compacte stat-tegel
- sec_div():         sectiescheidings-balk met emoji + lijn
- render_room_card():  gebruikt nu calc_room_status_smart() voor correcte status
- ynab_transfer_form(): herbruikbaar formulier voor envelope-transfers
- sidebar:           1 save-knop ipv 3 + backup viewer
"""
import streamlit as st
from utils.config import (
    CSS_STYLES, APP_CONFIG, CHART_COLORS,
    KAMER_EMOJIS, ROOM_STATUSES, ROOM_STATUS_COLORS,
)


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
    emoji_html = f"<span style='font-size:2rem;margin-right:12px;'>{emoji}</span>" if emoji else ""
    sub_html   = f"<p>{subtitle}</p>" if subtitle else ""
    st.markdown(f"""
    <div class="hdr ani">
      <div style='display:flex;align-items:center;'>
        {emoji_html}<div><h1>{title}</h1>{sub_html}</div>
      </div>
    </div>""", unsafe_allow_html=True)


# ── Section divider ────────────────────────────────────────────────────────

def sec_div(title: str, emoji: str = "📊") -> None:
    st.markdown(f"""
    <div class="sec-div">
      <span class="sec-emoji">{emoji}</span>
      <span class="sec-title">{title}</span>
      <div class="sec-line"></div>
    </div>
    """, unsafe_allow_html=True)


# ── Hero KPI (groot) ───────────────────────────────────────────────────────

def hero_kpi(label: str, value: str, sub: str = "", variant: str = "") -> None:
    """Voor de grote 'status in één oogopslag'-strip bovenaan."""
    alias = {"success":"grn","danger":"red","warning":"warn"}
    cls   = alias.get(variant, variant)
    sub_html = f'<div class="hero-sub">{sub}</div>' if sub else ""
    st.markdown(f"""
    <div class="hero {cls} ani">
      <div class="hero-lbl">{label}</div>
      <div class="hero-val">{value}</div>
      {sub_html}
    </div>""", unsafe_allow_html=True)


# ── Stat strip (klein compact) ─────────────────────────────────────────────

def stat_strip(emoji: str, value: str, label: str) -> None:
    st.markdown(f"""
    <div class="stat-strip ani">
      <span class="ss-emoji">{emoji}</span>
      <div class="ss-val">{value}</div>
      <div class="ss-lbl">{label}</div>
    </div>""", unsafe_allow_html=True)


# ── KPI card (medium) ──────────────────────────────────────────────────────

def kpi(label: str, value: str, sub: str = "", variant: str = "") -> None:
    alias = {"success":"grn","danger":"red","warning":"warn","neutral":"neu"}
    cls   = alias.get(variant, variant)
    sub_html = f'<div class="sub">{sub}</div>' if sub else ""
    st.markdown(f"""
    <div class="kpi {cls} ani">
      <div class="lbl">{label}</div>
      <div class="val">{value}</div>
      {sub_html}
    </div>""", unsafe_allow_html=True)


# ── Progress bar ───────────────────────────────────────────────────────────

def progress(label: str, pct: float, variant: str = "") -> None:
    p   = min(max(float(pct), 0), 100)
    cls = variant or ("red" if p >= 100 else "warn" if p >= 80 else "grn")
    st.markdown(f"""
    <div class="pgwrap">
      <div class="pglbl"><span>{label}</span><span>{p:.1f}%</span></div>
      <div class="pgbar"><div class="pgfill {cls}" style="width:{p}%;"></div></div>
    </div>""", unsafe_allow_html=True)


# ── Alert ──────────────────────────────────────────────────────────────────

def alert(msg: str, variant: str = "grn") -> None:
    st.markdown(f'<div class="alrt {variant}">{msg}</div>', unsafe_allow_html=True)


# ── Notion-stijl Kamer Card (smart status) ─────────────────────────────────

def render_room_card(
    naam: str,
    begroot: float,
    gerealiseerd: float,
    n_posten: int = 0,
    status: str = "",
    extra_caption: str = "",
) -> None:
    from utils.state import calc_room_status_smart

    pct       = min(gerealiseerd / begroot * 100, 100) if begroot > 0 else 0
    beschikb  = begroot - gerealiseerd
    emoji     = KAMER_EMOJIS.get(naam, "🏗️")
    auto_st   = calc_room_status_smart(begroot, gerealiseerd, n_posten)
    st_label  = status or auto_st
    st_icon   = ROOM_STATUSES.get(st_label, "📋")
    badge_cls = {"Planningsfase":"badge-plan","In uitvoering":"badge-wip",
                 "Klaar":"badge-done","On hold":"badge-hold"}.get(st_label,"badge-plan")
    bar_cls   = "red" if pct >= 100 else "warn" if pct >= 80 else "grn"
    rest_col  = "#10B981" if beschikb >= 0 else "#EF4444"
    rest_lbl  = "vrij" if beschikb >= 0 else "over"

    with st.container(border=True):
        st.markdown(f"""
        <div class="ani" style="padding:2px 0;">
          <span class="rc-emoji">{emoji}</span>
          <div class="rc-title">{naam}</div>
          <span class="badge {badge_cls}">{st_icon} {st_label}</span>
          <div class="pgwrap" style="margin-top:6px;">
            <div class="pglbl">
              <span style='font-size:.72rem;'>Voortgang</span>
              <span style='font-size:.72rem;font-weight:700;'>{pct:.0f}%</span>
            </div>
            <div class="pgbar">
              <div class="pgfill {bar_cls}" style="width:{pct:.1f}%;"></div>
            </div>
          </div>
        </div>""", unsafe_allow_html=True)

        c1, c2 = st.columns(2)
        c1.metric("Begroot",     f"€ {begroot:,.0f}")
        c2.metric("Beschikbaar",
                  f"€ {beschikb:,.0f}",
                  delta=f"{rest_lbl}",
                  delta_color="normal" if beschikb >= 0 else "inverse")

        cap = f"💸 € {gerealiseerd:,.0f} besteed · 📄 {n_posten} posten"
        if extra_caption:
            cap += f" · {extra_caption}"
        st.caption(cap)


# ── YNAB Envelope rij ──────────────────────────────────────────────────────

def render_ynab_row(env: dict) -> None:
    pct       = min(float(env.get("pct", 0)), 100)
    status    = env.get("status", "ok")
    bar_cls   = {"ok":"grn","warn":"warn","over":"red"}.get(status,"grn")
    amt_cls   = {"ok":"grn","warn":"warn","over":"red"}.get(status,"grn")
    beschikb  = env.get("beschikbaar", 0)
    type_icon = "🔨" if env.get("type") == "verbouwing" else "🛋️"
    naam      = env.get("naam","")
    emoji     = KAMER_EMOJIS.get(naam, "")
    override  = env.get("override", 0)
    override_html = ""
    if override != 0:
        sign = "+" if override > 0 else ""
        color = "#10B981" if override > 0 else "#EF4444"
        override_html = f"<span style='font-size:.65rem;color:{color};margin-left:6px;'>({sign}€{override:,.0f})</span>"

    st.markdown(f"""
    <div class="env-row">
      <span class="env-name">{type_icon} {emoji} {naam}{override_html}</span>
      <div class="env-bar">
        <div class="env-fill {bar_cls}" style="width:{pct:.1f}%;"></div>
      </div>
      <span style="font-size:.74rem;color:#9CA3AF;min-width:38px;text-align:center;">
        {pct:.0f}%
      </span>
      <span class="env-amt {amt_cls}">
        € {beschikb:,.0f}
      </span>
    </div>""", unsafe_allow_html=True)


# ── YNAB Transfer Form (Prio 3 kern!) ─────────────────────────────────────

def ynab_transfer_form(envelopes: list, vrije_buffer: float, key_prefix: str = "ynab_tf") -> None:
    """
    Interactief formulier om geld te verschuiven tussen envelopes en buffer.
    Aangeroepen vanuit app.py en pages/1_Verbouwing.py.
    """
    from utils.state import transfer_envelope, reset_envelope_overrides

    if not envelopes:
        alert("Geen envelopes beschikbaar voor transfer.", "warn")
        return

    # Bouw keuze-lijsten
    bron_opties = ["💎 Vrije Buffer"] + [
        f"{'🔨' if e['type']=='verbouwing' else '🛋️'} {KAMER_EMOJIS.get(e['naam'],'')} {e['naam']}"
        for e in envelopes
    ]
    doel_opties = ["💎 Vrije Buffer"] + [
        f"{'🔨' if e['type']=='verbouwing' else '🛋️'} {KAMER_EMOJIS.get(e['naam'],'')} {e['naam']}"
        for e in envelopes
    ]

    with st.form(f"{key_prefix}_form", clear_on_submit=True):
        st.markdown("##### 🔄 Verschuif geld tussen envelopes")
        st.caption("YNAB regel #3: 'Roll with the punches'. Verplaats budget tussen categorieën zonder de Excel handmatig aan te passen.")

        c1, c2, c3 = st.columns([2, 2, 1])
        with c1:
            bron_sel = st.selectbox("Vanaf", bron_opties, key=f"{key_prefix}_bron")
        with c2:
            doel_sel = st.selectbox("Naar", doel_opties, key=f"{key_prefix}_doel", index=1)
        with c3:
            bedrag = st.number_input("Bedrag (€)", min_value=0.0, step=100.0, format="%.2f",
                                     key=f"{key_prefix}_bedrag")
        notitie = st.text_input("Notitie (optioneel)",
                                placeholder="bijv. 'Extra reserve voor uitbouw'",
                                key=f"{key_prefix}_note")

        submitted = st.form_submit_button("💸 Verschuif", type="primary",
                                          use_container_width=True)
        if submitted:
            if bron_sel == doel_sel:
                st.error("Bron en doel moeten verschillen.")
            elif bedrag <= 0:
                st.error("Voer een bedrag in groter dan 0.")
            else:
                # Parse selectie naar (naam, type)
                def _parse_sel(sel: str) -> tuple[str, str]:
                    if "Vrije Buffer" in sel:
                        return ("buffer", "")
                    # Match envelope op exacte naam
                    for e in envelopes:
                        if e["naam"] in sel:
                            return (e["naam"], e["type"])
                    return ("", "")

                bron_naam, bron_type = _parse_sel(bron_sel)
                doel_naam, doel_type = _parse_sel(doel_sel)

                # Validatie: niet meer overdragen dan beschikbaar
                if bron_naam == "buffer":
                    if bedrag > vrije_buffer + 0.01:
                        st.error(f"Onvoldoende vrije buffer. Beschikbaar: € {vrije_buffer:,.2f}")
                        return
                else:
                    bron_env = next((e for e in envelopes if e["naam"] == bron_naam), None)
                    if bron_env and bedrag > bron_env["begroot"] + 0.01:
                        st.error(f"Onvoldoende budget in {bron_naam}. "
                                 f"Beschikbaar: € {bron_env['begroot']:,.2f}")
                        return

                ok, msg = transfer_envelope(
                    bron=bron_naam, bron_type=bron_type,
                    doel=doel_naam, doel_type=doel_type,
                    bedrag=bedrag, notitie=notitie,
                )
                if ok:
                    st.success(msg)
                    st.rerun()
                else:
                    st.error(msg)

    # Reset knop
    with st.expander("⚙️ Geavanceerd", expanded=False):
        st.caption("Wis alle overrides en herstel envelopes naar de oorspronkelijke Excel-begroting.")
        if st.button("🔄 Reset alle overrides", key=f"{key_prefix}_reset",
                     use_container_width=True):
            if reset_envelope_overrides():
                st.success("✅ Alle overrides gewist.")
                st.rerun()
            else:
                st.error("❌ Reset mislukt.")


# ── Sidebar (single-save flow) ─────────────────────────────────────────────

def sidebar(maand_tot: dict = None, project: dict = None) -> None:
    from utils.state import reload
    from utils.excel_handler import list_backups, restore_backup
    from utils.notifications import get_notification_counts

    mt = maand_tot or {}
    pj = project   or {}

    with st.sidebar:
        # Notificatie badge
        try:
            nc = get_notification_counts()
            badge_html = ""
            if nc["kritiek"] > 0:
                badge_html = f"<span style='background:#EF4444;color:#fff;font-size:.65rem;font-weight:700;padding:1px 6px;border-radius:999px;margin-left:6px;'>{nc['kritiek']} !</span>"
            elif nc["warn"] > 0:
                badge_html = f"<span style='background:#F59E0B;color:#fff;font-size:.65rem;font-weight:700;padding:1px 6px;border-radius:999px;margin-left:6px;'>{nc['warn']}</span>"
        except Exception:
            badge_html = ""

        st.markdown(f"""
        <div style='text-align:center;padding:10px 0 6px;'>
          <div style='font-size:2.6rem;'>🏠</div>
          <div style='font-size:.95rem;font-weight:800;color:#FFD700;letter-spacing:.04em;'>
            HOFAKKERS 44{badge_html}</div>
          <div style='font-size:.65rem;color:#9CA3AF;letter-spacing:.1em;margin-top:1px;'>
            Patrick & Willianne · v4.0</div>
        </div>""", unsafe_allow_html=True)

        st.markdown("---")
        st.markdown("#### 🏗️ Project")
        st.metric("Verbouwing",     f"€ {pj.get('verbouwing',0):,.0f}")
        st.metric("Inboedel",       f"€ {pj.get('inboedel',0):,.0f}")
        st.metric("Totaal project",  f"€ {pj.get('project',0):,.0f}")

        st.markdown("---")
        st.markdown("#### 💳 Cashflow /maand")
        ink    = mt.get("inkomen", 0)
        uit    = mt.get("totaal_uitgaven", 0)
        ruimte = mt.get("ruimte", 0)
        st.metric("Inkomen",  f"€ {ink:,.0f}")
        st.metric("Uitgaven", f"€ {uit:,.0f}")
        st.metric("Buffer",   f"€ {ruimte:,.0f}",
                  delta_color="normal" if ruimte >= 0 else "inverse")
        if ink > 0:
            pct = min(uit / ink * 100, 100)
            bc  = "#EF4444" if pct > 85 else "#F59E0B" if pct > 70 else "#10B981"
            st.markdown(f"""
            <div style='margin:2px 0 12px;'>
              <div style='background:rgba(255,255,255,.12);border-radius:999px;height:6px;'>
                <div style='width:{pct:.1f}%;height:100%;background:{bc};border-radius:999px;'></div>
              </div>
              <div style='font-size:.66rem;color:#9CA3AF;margin-top:2px;text-align:right;'>
                {pct:.0f}% van inkomen</div>
            </div>""", unsafe_allow_html=True)

        st.markdown("---")
        st.markdown("#### 💎 Vermogen na verbouwing")
        st.metric("Patrick",   f"€ {pj.get('patrick',0):,.0f}")
        st.metric("Willianne", f"€ {pj.get('willianne',0):,.0f}")
        st.metric("Samen",     f"€ {pj.get('samen',0):,.0f}")

        st.markdown("---")
        st.markdown("#### 🔄 Data & Backups")
        if st.button("🔄 Herladen uit Excel", use_container_width=True):
            reload()
            st.success("✅ Verse data geladen!")
            st.rerun()

        with st.expander("💾 Backup-historie"):
            backups = list_backups()
            if backups:
                st.caption(f"Laatste {len(backups)} backups (max 10)")
                for bak in backups[:5]:
                    ts_str = bak.stem.replace("Begroting_", "")
                    try:
                        from datetime import datetime
                        dt = datetime.strptime(ts_str, "%Y%m%d_%H%M%S")
                        label = dt.strftime("%d-%m %H:%M")
                    except ValueError:
                        label = ts_str
                    if st.button(f"↩️ Herstel {label}",
                                 key=f"restore_{ts_str}",
                                 use_container_width=True):
                        if restore_backup(bak):
                            reload()
                            st.success(f"✅ Hersteld naar {label}")
                            st.rerun()
            else:
                st.caption("Geen backups (worden bij elke save gemaakt)")

        st.markdown("---")
        st.caption("Hofakkers 44 · v3.0 · Auto-save naar Excel")
