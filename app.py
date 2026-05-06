"""
app.py  –  Hofakkers 44  v4.0
Landingspagina – "alles in één oogopslag":

LAYOUT:
  0. Notificatiebalk (kritieke meldingen)
  1. HERO strip      → 3 grote KPI's
  2. STAT strip      → 6 compacte stats
  3. Planning voortgang snippet
  4. Notion Gallery  → Verbouwingscategorieën
  5. Notion Gallery  → Inboedel kamers
  6. YNAB Transfer
  7. Budget vs Actuals
  8. Cashflow + Vermogen
  9. Projectinstellingen (collapsed)
"""
import streamlit as st
import pandas as pd
import plotly.graph_objects as go

from utils.ui import (
    page_setup, header, kpi, hero_kpi, stat_strip, sec_div, progress,
    sidebar, render_room_card, render_ynab_row, ynab_transfer_form, alert,
)
from utils.state import (
    init, dash, set_dashboard,
    calc_maand_totalen, calc_project,
    calc_verbouwing_totalen, calc_inboedel_totalen,
    calc_spaargeld, calc_ynab_envelopes, calc_budget_vs_actuals,
)
from utils.config import CHART_COLORS, KAMER_EMOJIS
from utils.excel_handler import save_dashboard
from utils.planning import init_planning, get_planning_stats
from utils.notifications import render_notification_bar, get_notification_counts

# ── Bootstrap ───────────────────────────────────────────────────────────────
page_setup("🏠 Hofakkers 44 – Dashboard")
init()
init_planning()

mt   = calc_maand_totalen()
proj = calc_project()
verm = calc_spaargeld()
verb = calc_verbouwing_totalen()
inbo = calc_inboedel_totalen()
ynab = calc_ynab_envelopes()
bva  = calc_budget_vs_actuals()
plan_stats = get_planning_stats()
notif_counts = get_notification_counts()

sidebar(mt, proj)

header("Hofakkers 44 – Renovatie Dashboard",
       "Real-time · Patrick & Willianne · Elke euro krijgt een taak",
       "🏠")

# ── Notificatiebalk ──────────────────────────────────────────────────────────
if notif_counts["totaal"] > 0:
    render_notification_bar(max_visible=2)
    col_notif, _ = st.columns([2, 5])
    with col_notif:
        st.page_link("pages/0_Meldingen.py",
                     label=f"🔔 Bekijk alle {notif_counts['totaal']} meldingen →",
                     help="Open de volledige meldingenpagina")

# ══════════════════════════════════════════════════════════════════════════════
# 1. HERO STRIP — STATUS IN ÉÉN OOGOPSLAG
# ══════════════════════════════════════════════════════════════════════════════
sec_div("Status in één oogopslag", "🎯")

h1, h2, h3 = st.columns(3)

# Hero 1: Totaal Project
project_total = proj["project"]
real_total    = bva["Gerealiseerd (€)"].sum() if not bva.empty else 0
pct_done      = (real_total / project_total * 100) if project_total > 0 else 0
with h1:
    hero_kpi(
        "🏗️ Totaal Project",
        f"€ {project_total:,.0f}",
        f"€ {real_total:,.0f} besteed · {pct_done:.0f}% voortgang",
    )

# Hero 2: Vrije Buffer (YNAB)
vrij = ynab["vrij"]
inleg = ynab["totaal_inleg"]
toegew = ynab["toegewezen"]
buf_pct = (toegew / inleg * 100) if inleg > 0 else 0
with h2:
    if vrij > 0:
        hero_kpi(
            "💎 Vrije Buffer",
            f"€ {vrij:,.0f}",
            f"{buf_pct:.0f}% van € {inleg:,.0f} toegewezen · klaar om toe te wijzen",
            "grn",
        )
    elif vrij == 0:
        hero_kpi("💎 Vrije Buffer", "€ 0", "Volledig toegewezen", "warn")
    else:
        hero_kpi("⚠️ Tekort", f"€ {abs(vrij):,.0f}",
                 f"Begroot ({toegew:,.0f}) > Beschikbaar ({inleg:,.0f})", "red")

# Hero 3: Maandelijkse Buffer
ruimte = mt.get("ruimte", 0)
ink    = mt.get("inkomen", 0)
with h3:
    if ruimte > 0:
        hero_kpi(
            "💰 Maand Buffer",
            f"€ {ruimte:,.0f}",
            f"per maand vrij van € {ink:,.0f} inkomen",
            "grn",
        )
    elif ruimte == 0:
        hero_kpi("💰 Maand Buffer", "€ 0", "Inkomen volledig besteed", "warn")
    else:
        hero_kpi("⚠️ Tekort", f"€ {abs(ruimte):,.0f}",
                 "uitgaven overschrijden inkomen", "red")

# Voortgangsbalk onder hero
st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
if inleg > 0:
    progress(f"💎 Budget toegewezen ({buf_pct:.0f}%) · "
             f"€ {toegew:,.0f} / € {inleg:,.0f}", buf_pct)

# ══════════════════════════════════════════════════════════════════════════════
# 2. STAT STRIP — SECONDAIRE METRICS
# ══════════════════════════════════════════════════════════════════════════════
st.markdown("<div style='height:6px'></div>", unsafe_allow_html=True)
s1, s2, s3, s4, s5, s6 = st.columns(6)
with s1: stat_strip("👤", f"€ {verm['patrick']:,.0f}",   "Patrick")
with s2: stat_strip("👤", f"€ {verm['willianne']:,.0f}", "Willianne")
with s3: stat_strip("🔨", f"€ {proj['verbouwing']:,.0f}", "Verbouwing")
with s4: stat_strip("🛋️", f"€ {proj['inboedel']:,.0f}",  "Inboedel")
with s5: stat_strip("💹", f"€ {mt.get('sparen',0):,.0f}", "Sparen/mnd")
with s6: stat_strip("🏦", f"€ {verm['totaal_sparen']:,.0f}", "Nu Gespaard")

# ── Planning snippet ──────────────────────────────────────────────────────────
if plan_stats["totaal"] > 0:
    st.markdown("<div style='height:6px'></div>", unsafe_allow_html=True)
    p1, p2, p3, p4 = st.columns([3, 1, 1, 1])
    with p1:
        progress(f"📅 Planning voortgang — {plan_stats['gereed']}/{plan_stats['totaal']} taken gereed",
                 plan_stats["pct"])
    with p2:
        st.metric("🟡 Bezig", plan_stats["bezig"])
    with p3:
        st.metric("⚪ Gepland", plan_stats["gepland"])
    with p4:
        if plan_stats["onhold"] > 0:
            st.metric("🔴 On Hold", plan_stats["onhold"])

# ══════════════════════════════════════════════════════════════════════════════
# 3. NOTION GALLERY — VERBOUWING
# ══════════════════════════════════════════════════════════════════════════════
sec_div("Verbouwing per Categorie", "🔨")

verb_cats = verb.get("categorieën", {})
if verb_cats:
    cats_sorted = sorted(verb_cats.items(), key=lambda x: -x[1])
    cols = st.columns(3)
    df_v = st.session_state.get("verbouwing", pd.DataFrame())

    for i, (cat, begroot) in enumerate(cats_sorted):
        env_match = next((e for e in ynab["envelopes"]
                          if e["naam"] == cat and e["type"] == "verbouwing"), None)
        gerealiseerd = env_match["gerealiseerd"] if env_match else 0.0
        n_posten = int(df_v[df_v["Categorie"] == cat].shape[0]) \
                   if not df_v.empty and "Categorie" in df_v.columns else 0
        override = env_match["override"] if env_match else 0
        extra = ""
        if override != 0:
            sign = "+" if override > 0 else ""
            extra = f"⚙️ override {sign}€{override:,.0f}"
        with cols[i % 3]:
            render_room_card(
                naam=cat, begroot=begroot,
                gerealiseerd=gerealiseerd, n_posten=n_posten,
                extra_caption=extra,
            )
else:
    alert("Geen verbouwingsdata. Controleer tabblad 'Verbouwing begroting'.", "warn")

# ══════════════════════════════════════════════════════════════════════════════
# 4. NOTION GALLERY — INBOEDEL
# ══════════════════════════════════════════════════════════════════════════════
sec_div("Inboedel per Kamer", "🛋️")

inbo_cats = inbo.get("categorieën", {})
if inbo_cats:
    cats_sorted_i = sorted(inbo_cats.items(), key=lambda x: -x[1])
    cols_i = st.columns(3)
    df_i = st.session_state.get("inboedel", pd.DataFrame())

    for i, (cat, begroot) in enumerate(cats_sorted_i):
        env_match = next((e for e in ynab["envelopes"]
                          if e["naam"] == cat and e["type"] == "inboedel"), None)
        gerealiseerd = env_match["gerealiseerd"] if env_match else 0.0
        n_posten = int(df_i[df_i["Categorie"] == cat].shape[0]) \
                   if not df_i.empty and "Categorie" in df_i.columns else 0
        override = env_match["override"] if env_match else 0
        extra = ""
        if override != 0:
            sign = "+" if override > 0 else ""
            extra = f"⚙️ override {sign}€{override:,.0f}"
        with cols_i[i % 3]:
            render_room_card(
                naam=cat, begroot=begroot,
                gerealiseerd=gerealiseerd, n_posten=n_posten,
                extra_caption=extra,
            )
else:
    alert("Geen inboedeldata. Controleer tabblad 'Inboedel begroting'.", "warn")

# ══════════════════════════════════════════════════════════════════════════════
# 5. YNAB TRANSFER — INTERACTIEF GELD VERSCHUIVEN
# ══════════════════════════════════════════════════════════════════════════════
sec_div("YNAB · Verschuif tussen envelopes", "🔄")

with st.expander("💸 Verschuif geld tussen categorieën (klik om te openen)", expanded=False):
    ynab_transfer_form(
        envelopes=ynab["envelopes"],
        vrije_buffer=ynab["vrij"],
        key_prefix="main_ynab",
    )

# Compacte envelope overview ernaast
col_v_env, col_i_env = st.columns(2)
verb_envs = [e for e in ynab["envelopes"] if e["type"] == "verbouwing"]
inbo_envs = [e for e in ynab["envelopes"] if e["type"] == "inboedel"]

with col_v_env:
    st.markdown("**🔨 Verbouwing envelopes**")
    if verb_envs:
        for e in verb_envs:
            render_ynab_row(e)

with col_i_env:
    st.markdown("**🛋️ Inboedel envelopes**")
    if inbo_envs:
        for e in inbo_envs:
            render_ynab_row(e)

# ══════════════════════════════════════════════════════════════════════════════
# 6. HOMEZADA — BUDGET VS ACTUALS
# ══════════════════════════════════════════════════════════════════════════════
sec_div("Budget vs Gerealiseerd (HomeZada)", "📊")

if not bva.empty:
    def _kleur_verschil(val):
        if isinstance(val,(int,float)):
            return "color:#10B981;font-weight:600" if val>0 else \
                   "color:#EF4444;font-weight:600" if val<0 else ""
        return ""

    styled = (
        bva.style
           .format({"Begroot (€)":"€ {:,.0f}","Gerealiseerd (€)":"€ {:,.0f}",
                    "Verschil (€)":"€ {:,.0f}","% Gebruikt":"{:.1f}%"})
           .map(_kleur_verschil, subset=["Verschil (€)"])
           .background_gradient(subset=["% Gebruikt"], cmap="RdYlGn_r", vmin=0, vmax=110)
    )
    st.dataframe(styled, use_container_width=True, hide_index=True, height=380)

    tc1, tc2, tc3 = st.columns(3)
    tc1.metric("Totaal Begroot",      f"€ {bva['Begroot (€)'].sum():,.0f}")
    tc2.metric("Totaal Gerealiseerd", f"€ {bva['Gerealiseerd (€)'].sum():,.0f}")
    versch = bva["Verschil (€)"].sum()
    tc3.metric("Totaal Beschikbaar", f"€ {versch:,.0f}",
               delta="✓ on track" if versch >= 0 else "⚠️ over budget",
               delta_color="normal" if versch >= 0 else "inverse")
else:
    alert("Nog geen uitgaven geregistreerd. Ga naar 🔨 Verbouwing → tab 'Uitgaven Registreren'.", "blu")

# ══════════════════════════════════════════════════════════════════════════════
# 7. CASHFLOW + VERMOGEN
# ══════════════════════════════════════════════════════════════════════════════
sec_div("Cashflow & Vermogen", "💳")

col_cf, col_verm = st.columns([3, 2])

with col_cf:
    vaste = mt.get("vaste", 0)
    var   = mt.get("variabel", 0)
    spar  = mt.get("sparen", 0)
    ruim  = mt.get("ruimte", 0)

    cf1, cf2, cf3, cf4 = st.columns(4)
    with cf1: kpi("💰 Inkomen",  f"€ {ink:,.0f}",   "/maand")
    with cf2: kpi("🏠 Vast",     f"€ {vaste:,.0f}",  "wonen+verzek")
    with cf3: kpi("🛒 Variabel", f"€ {var:,.0f}",    "boodsch+vrij")
    with cf4: kpi("💹 Sparen",   f"€ {spar:,.0f}",   "/maand", "grn")

    if ink > 0:
        progress("Uitgaven als % van inkomen",
                 mt.get("totaal_uitgaven",0)/ink*100)

    data_d = {"Wonen & vast":vaste,"Variabel":var,"Sparen":spar,"Buffer":max(ruim,0)}
    data_d = {k:v for k,v in data_d.items() if v > 0}
    if data_d:
        fig = go.Figure(go.Pie(
            labels=list(data_d.keys()), values=list(data_d.values()),
            hole=0.55, marker_colors=["#FF8C00","#FFD700","#10B981","#3B82F6"],
            textinfo="label+percent",
            hovertemplate="<b>%{label}</b><br>€ %{value:,.0f}/maand<extra></extra>",
        ))
        fig.update_layout(
            plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
            showlegend=False, margin=dict(l=0,r=0,t=0,b=0), height=260,
            annotations=[dict(text=f"<b>€{ink:,.0f}</b><br>/maand",
                              x=0.5,y=0.5,font_size=12,showarrow=False)],
        )
        st.plotly_chart(fig, use_container_width=True)

with col_verm:
    st.markdown("**💎 Vermogen na Verbouwing**")
    st.markdown("<div style='height:6px'></div>", unsafe_allow_html=True)
    kpi("👤 Patrick",   f"€ {verm['patrick']:,.0f}",   "resterend", "blu")
    st.markdown("<div style='height:6px'></div>", unsafe_allow_html=True)
    kpi("👤 Willianne", f"€ {verm['willianne']:,.0f}", "resterend", "grn")
    st.markdown("<div style='height:6px'></div>", unsafe_allow_html=True)
    kpi("💎 Samen",     f"€ {verm['samen']:,.0f}",     "gezamenlijk")

# ══════════════════════════════════════════════════════════════════════════════
# 8. PROJECTINSTELLINGEN (collapsed)
# ══════════════════════════════════════════════════════════════════════════════
with st.expander("⚙️ Projectinstellingen aanpassen (Dashboard PRO)", expanded=False):
    st.caption("Wijzigingen worden direct opgeslagen naar Excel — geen aparte 'app/excel' save meer.")
    d_data = dash()
    if d_data:
        df_dash = pd.DataFrame(list(d_data.items()), columns=["Instelling","Waarde"])
        edited  = st.data_editor(
            df_dash,
            column_config={
                "Instelling": st.column_config.TextColumn("Instelling", width="large", disabled=True),
                "Waarde":     st.column_config.TextColumn("Waarde",     width="medium"),
            },
            num_rows="fixed", use_container_width=True,
            key="editor_dash_main",
        )
        if st.button("💾 Opslaan", type="primary", key="save_dash_main"):
            new_d = {}
            for _, row in edited.iterrows():
                k = str(row["Instelling"]).strip()
                if k and k.lower() != "nan":
                    try:
                        new_d[k] = float(str(row["Waarde"]).replace(",",".").replace("€","").strip())
                    except (TypeError, ValueError):
                        new_d[k] = row["Waarde"]
            set_dashboard(new_d)
            if save_dashboard(new_d):
                st.success("✅ Opgeslagen naar Excel (backup gemaakt)")
                st.rerun()
            else:
                st.error("❌ Opslaan mislukt — is Excel geopend?")
    else:
        alert("Geen dashboard-data. Controleer tabblad 'Dashboard PRO' in Excel.", "warn")
