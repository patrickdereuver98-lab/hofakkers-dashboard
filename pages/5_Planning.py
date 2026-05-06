"""
pages/5_Planning.py  –  Hofakkers 44  v4.0

Planning & Tijdlijn:
  - Gantt chart (Plotly)
  - Drag & Drop kaarten (herschikken via ▲▼ knoppen + direct springen)
  - Status in-place bijwerken
  - Koppeling met verbouwingscategorieën (YNAB envelopes)
  - Deadlines triggeren notificaties
"""
import streamlit as st
import pandas as pd
from datetime import date, timedelta
import plotly.express as px
import plotly.graph_objects as go

from utils.ui import page_setup, header, kpi, progress, sidebar, alert, sec_div
from utils.state import init, calc_maand_totalen, calc_project, calc_ynab_envelopes
from utils.planning import (
    init_planning, get_planning, save_planning,
    move_up, move_down, move_to_position,
    add_stap, delete_stap, update_status,
    get_planning_stats, get_gantt_data,
    STATUSSEN, PRIORITEITEN, STATUS_COLORS, STATUS_ICONS, PRIO_ICONS,
)
from utils.notifications import render_notification_bar
from utils.config import CHART_COLORS, VERB_CATS, INBOEDEL_CATS

page_setup("📅 Planning – Hofakkers 44")
init()
init_planning()

sidebar(calc_maand_totalen(), calc_project())
header("📅 Renovatie Planning", "Gantt · Drag & Drop · Gekoppeld aan budget", "📅")

# ── Notificaties (planning-specifiek) ───────────────────────────────────────
render_notification_bar(max_visible=3, filter_page="Planning")

# ── KPI Strip ───────────────────────────────────────────────────────────────
stats = get_planning_stats()
c1, c2, c3, c4, c5 = st.columns(5)
with c1: kpi("📋 Totaal Taken",   str(stats["totaal"]),  "in planning")
with c2: kpi("🟢 Gereed",         str(stats["gereed"]),  f"{stats['pct']:.0f}% klaar", "grn")
with c3: kpi("🟡 Bezig",          str(stats["bezig"]),   "in uitvoering", "warn")
with c4: kpi("⚪ Gepland",         str(stats["gepland"]), "nog te starten")
with c5: kpi("🔴 On Hold",        str(stats["onhold"]),  "geblokkeerd",
             "red" if stats["onhold"] > 0 else "")

if stats["totaal"] > 0:
    progress("Algehele voortgang", stats["pct"])

st.markdown("---")

tabs = st.tabs([
    "📅 Gantt Chart",
    "🃏 Taken Kaarten",
    "🔄 Herschikken",
    "➕ Nieuwe Taak",
    "📝 Bulk Editor",
])

planning = get_planning()


# ══════════════════════════════════════════════════════════════════════════════
# TAB 1: GANTT CHART
# ══════════════════════════════════════════════════════════════════════════════
with tabs[0]:
    sec_div("Tijdlijn — Gantt Chart", "📅")

    if not planning:
        alert("Geen planningsstappen beschikbaar.", "warn")
    else:
        df_gantt = get_gantt_data()
        if not df_gantt.empty:
            # Kleurmapping op status
            kleur_map = {
                "Gepland":        "#94A3B8",
                "Gestart":        "#3B82F6",
                "In uitvoering":  "#F59E0B",
                "Wacht op ander": "#8B5CF6",
                "Gereed":         "#10B981",
                "On hold":        "#EF4444",
            }

            fig = px.timeline(
                df_gantt,
                x_start="Start",
                x_end="Finish",
                y="Task",
                color="Status",
                color_discrete_map=kleur_map,
                hover_data=["Resource","Prio"],
                labels={"Task":"Taak","Resource":"Categorie","Status":"Status"},
            )
            fig.update_yaxes(autorange="reversed", tickfont=dict(size=10))
            fig.update_layout(
                plot_bgcolor="rgba(0,0,0,0)",
                paper_bgcolor="rgba(0,0,0,0)",
                xaxis=dict(
                    title="",
                    showgrid=True,
                    gridcolor="#F3F4F6",
                    tickformat="%d-%m",
                ),
                yaxis=dict(title=""),
                legend=dict(orientation="h", y=-0.15, title=""),
                margin=dict(l=0, r=0, t=10, b=60),
                height=max(320, len(df_gantt) * 28 + 80),
                font=dict(family="Inter", size=11),
            )
            # Vandaag-lijn via add_shape (fix: add_vline geeft TypeError met
            # pandas Timestamp-objecten die px.timeline aanmaakt)
            today_str = str(date.today())
            fig.add_shape(
                type="line",
                x0=today_str, x1=today_str,
                y0=0, y1=1, yref="paper",
                line=dict(color="#EF4444", width=2, dash="dash"),
            )
            fig.add_annotation(
                x=today_str, y=1.02, yref="paper",
                text="📅 Vandaag",
                showarrow=False,
                font=dict(color="#EF4444", size=11, weight=700),
                xanchor="center",
            )
            st.plotly_chart(fig, use_container_width=True)

            # Legenda
            st.caption("🔴 Vandaag-lijn | Hover over een balk voor details")

            # Kritiek pad
            with st.expander("🔍 Kritiek Pad & Afhankelijkheden"):
                afh_data = [
                    (p["Taak"], p["Afhankelijk_Van"], p["Status"])
                    for p in planning if p.get("Afhankelijk_Van")
                ]
                if afh_data:
                    df_afh = pd.DataFrame(afh_data,
                                          columns=["Taak","Afhankelijk van","Status"])
                    st.dataframe(df_afh, use_container_width=True, hide_index=True)
                else:
                    st.info("Geen afhankelijkheden ingesteld.")
        else:
            alert("Geen datums ingevuld — voeg startdatum/deadline toe via de Bulk Editor.", "blu")


# ══════════════════════════════════════════════════════════════════════════════
# TAB 2: TAKEN KAARTEN (Notion-stijl, gefilterd per status)
# ══════════════════════════════════════════════════════════════════════════════
with tabs[1]:
    sec_div("Taken Overzicht", "🃏")

    # Filter controls
    f1, f2, f3 = st.columns([2, 2, 2])
    with f1:
        filter_status = st.multiselect(
            "Filter op Status",
            STATUSSEN,
            default=[s for s in STATUSSEN if s != "Gereed"],
            key="filter_status_kaarten",
        )
    with f2:
        filter_cat = st.multiselect(
            "Filter op Categorie",
            sorted(set(p["Categorie"] for p in planning)),
            key="filter_cat_kaarten",
        )
    with f3:
        filter_prio = st.multiselect(
            "Filter op Prioriteit",
            PRIORITEITEN,
            key="filter_prio_kaarten",
        )

    filtered = planning.copy()
    if filter_status:
        filtered = [p for p in filtered if p["Status"] in filter_status]
    if filter_cat:
        filtered = [p for p in filtered if p["Categorie"] in filter_cat]
    if filter_prio:
        filtered = [p for p in filtered if p["Prioriteit"] in filter_prio]

    if not filtered:
        alert("Geen taken gevonden met deze filters.", "blu")
    else:
        # Groepeer per status-kolom (Kanban)
        kanban_order = ["In uitvoering", "Gestart", "Gepland", "Wacht op ander", "On hold", "Gereed"]
        groepen = {s: [p for p in filtered if p["Status"] == s] for s in kanban_order}
        groepen = {s: taken for s, taken in groepen.items() if taken}

        for status_naam, taken in groepen.items():
            kleur = STATUS_COLORS.get(status_naam, "#6B7280")
            icon  = STATUS_ICONS.get(status_naam, "⚪")
            st.markdown(f"""
            <div style='display:flex;align-items:center;gap:8px;margin:14px 0 8px;'>
              <span style='font-size:1.1rem;'>{icon}</span>
              <span style='font-weight:700;color:{kleur};font-size:.95rem;'>{status_naam}</span>
              <span style='background:{kleur}22;color:{kleur};font-size:.68rem;
                           font-weight:700;padding:1px 8px;border-radius:999px;'>
                {len(taken)}</span>
            </div>""", unsafe_allow_html=True)

            cols = st.columns(min(len(taken), 3))
            for ci, p in enumerate(taken):
                idx = planning.index(p)  # echte index in planning
                with cols[ci % 3]:
                    today = date.today()
                    deadline_str = str(p.get("Deadline", "") or "")
                    deadline_color = "#6B7280"
                    deadline_icon  = "📅"
                    try:
                        dl = date.fromisoformat(deadline_str)
                        if dl < today and p["Status"] != "Gereed":
                            deadline_color = "#EF4444"
                            deadline_icon  = "🚨"
                        elif dl <= today + timedelta(days=7) and p["Status"] != "Gereed":
                            deadline_color = "#F59E0B"
                            deadline_icon  = "⚡"
                    except ValueError:
                        pass

                    prio_icon = PRIO_ICONS.get(p.get("Prioriteit","Normaal"), "🔵")
                    afh = p.get("Afhankelijk_Van", "")

                    with st.container(border=True):
                        st.markdown(f"""
                        <div class='ani' style='padding:2px 0;'>
                          <div style='font-weight:700;font-size:.88rem;color:#1A1A2E;
                                      margin-bottom:5px;'>{p["Taak"]}</div>
                          <div style='font-size:.72rem;color:#6B7280;display:flex;
                                      flex-wrap:wrap;gap:6px;'>
                            <span>📁 {p["Categorie"]}</span>
                            <span>👤 {p.get("Verantwoordelijke","—")}</span>
                            <span style='color:{deadline_color};'>{deadline_icon} {deadline_str[:10]}</span>
                            <span>{prio_icon} {p.get("Prioriteit","")}</span>
                            {f'<span>🔗 {afh[:20]}</span>' if afh else ''}
                          </div>
                          {f'<div style="font-size:.7rem;color:#6B7280;margin-top:4px;font-style:italic;">{p.get("Notities","")[:60]}...</div>' if p.get("Notities","") else ""}
                        </div>""", unsafe_allow_html=True)

                        # Quick status-update
                        new_st = st.selectbox(
                            "Status wijzigen",
                            STATUSSEN,
                            index=STATUSSEN.index(p["Status"]) if p["Status"] in STATUSSEN else 0,
                            key=f"st_sel_{idx}",
                            label_visibility="collapsed",
                        )
                        if new_st != p["Status"]:
                            update_status(idx, new_st)
                            st.rerun()

                        if st.button("🗑️ Verwijder", key=f"del_kaart_{idx}",
                                     use_container_width=True):
                            delete_stap(idx)
                            st.success("✅ Verwijderd")
                            st.rerun()


# ══════════════════════════════════════════════════════════════════════════════
# TAB 3: HERSCHIKKEN — Drag & Drop via ▲▼ knoppen + spring-naar-positie
# ══════════════════════════════════════════════════════════════════════════════
with tabs[2]:
    sec_div("Volgorde aanpassen — Sleep & Drop", "🔄")
    st.caption("Gebruik ▲▼ om stappen te verplaatsen, of typ een doelpositie voor direct springen.")

    if not planning:
        alert("Geen planningsstappen.", "warn")
    else:
        # Instructie
        alert("💡 Klik ▲ of ▼ om een stap te verplaatsen. "
              "Je kunt ook de nummerveld gebruiken om direct naar een positie te springen.", "blu")

        st.markdown("<div style='height:4px'></div>", unsafe_allow_html=True)

        for idx, stap in enumerate(planning):
            kleur = STATUS_COLORS.get(stap["Status"], "#6B7280")
            icon  = STATUS_ICONS.get(stap["Status"], "⚪")
            prio_icon = PRIO_ICONS.get(stap.get("Prioriteit","Normaal"), "🔵")

            c_num, c_card, c_up, c_down, c_jump = st.columns([0.5, 6, 0.5, 0.5, 1.2])

            with c_num:
                st.markdown(f"""
                <div style='background:#F9FAFB;border-radius:6px;padding:6px;
                             text-align:center;font-weight:700;font-size:.8rem;
                             color:#6B7280;margin-top:8px;'>{idx+1}</div>""",
                             unsafe_allow_html=True)

            with c_card:
                st.markdown(f"""
                <div class='plan-card status-{stap["Status"].lower().replace(" ","")}' style='
                     border-left-color:{kleur};'>
                  <div class='pc-title'>{icon} {stap["Taak"]}</div>
                  <div class='pc-meta'>
                    <span>📁 {stap["Categorie"]}</span>
                    <span>👤 {stap.get("Verantwoordelijke","—")}</span>
                    <span>📅 {str(stap.get("Deadline",""))[:10]}</span>
                    <span>{prio_icon} {stap.get("Prioriteit","")}</span>
                    {f'<span>🔗 {stap.get("Afhankelijk_Van","")[:20]}</span>' if stap.get("Afhankelijk_Van") else ""}
                  </div>
                </div>""", unsafe_allow_html=True)

            with c_up:
                if idx > 0:
                    if st.button("▲", key=f"up_{idx}", help=f"Verplaats naar positie {idx}",
                                 use_container_width=True):
                        move_up(idx)
                        st.success(f"✅ '{stap['Taak']}' naar boven verplaatst")
                        st.rerun()

            with c_down:
                if idx < len(planning) - 1:
                    if st.button("▼", key=f"dn_{idx}", help=f"Verplaats naar positie {idx+2}",
                                 use_container_width=True):
                        move_down(idx)
                        st.success(f"✅ '{stap['Taak']}' naar beneden verplaatst")
                        st.rerun()

            with c_jump:
                target = st.number_input(
                    "→ pos",
                    min_value=1, max_value=len(planning),
                    value=idx + 1,
                    step=1, key=f"jump_{idx}",
                    label_visibility="collapsed",
                )
                if int(target) != idx + 1:
                    if st.button("↩️", key=f"jump_btn_{idx}", help="Spring naar positie",
                                 use_container_width=True):
                        move_to_position(idx, int(target) - 1)
                        st.success(f"✅ Verplaatst naar positie {int(target)}")
                        st.rerun()

        st.markdown("---")
        if st.button("💾 Opslaan volgorde naar Excel", type="primary",
                     use_container_width=True, key="save_volgorde"):
            save_planning(planning)
            st.success("✅ Volgorde opgeslagen naar Excel!")


# ══════════════════════════════════════════════════════════════════════════════
# TAB 4: NIEUWE TAAK TOEVOEGEN
# ══════════════════════════════════════════════════════════════════════════════
with tabs[3]:
    sec_div("Nieuwe Taak Toevoegen", "➕")

    # Automatische suggestie: volgende logische stap
    gereed_cats = set(p["Categorie"] for p in planning if p["Status"] == "Gereed")
    alle_cats   = set(p["Categorie"] for p in planning)
    volgende_cat = next((c for c in VERB_CATS if c in alle_cats and c not in gereed_cats),
                        VERB_CATS[0] if VERB_CATS else "")

    with st.form("nieuw_stap_form", clear_on_submit=True):
        r1c1, r1c2 = st.columns(2)
        with r1c1:
            taak = st.text_input("Taaknaam *", placeholder="bijv. 'Vloer egaliseren'")
            categorie = st.selectbox(
                "Categorie (gekoppeld aan budget)",
                VERB_CATS + INBOEDEL_CATS + ["Overig"],
                index=VERB_CATS.index(volgende_cat) if volgende_cat in VERB_CATS else 0,
            )
            verant = st.text_input("Verantwoordelijke", placeholder="bijv. 'Patrick'")
        with r1c2:
            start   = st.date_input("Startdatum",  value=date.today())
            deadline = st.date_input("Deadline",   value=date.today() + timedelta(days=7))
            status  = st.selectbox("Status", STATUSSEN, index=0)
            prioriteit = st.selectbox("Prioriteit", PRIORITEITEN, index=1)

        r2c1, r2c2 = st.columns(2)
        with r2c1:
            afh = st.selectbox(
                "Afhankelijk van (optioneel)",
                ["— geen —"] + [p["Taak"] for p in planning],
                index=0,
            )
        with r2c2:
            notities = st.text_area("Notities (optioneel)", height=80)

        submitted = st.form_submit_button("➕ Toevoegen", type="primary",
                                          use_container_width=True)
        if submitted:
            if not taak.strip():
                st.error("Voer een taaknaam in.")
            elif deadline < start:
                st.error("Deadline moet na startdatum liggen.")
            else:
                afh_val = "" if afh == "— geen —" else afh
                add_stap(
                    taak=taak.strip(), categorie=categorie, verant=verant,
                    start=str(start), deadline=str(deadline),
                    status=status, prioriteit=prioriteit,
                    afh=afh_val, notities=notities,
                )
                st.success(f"✅ Taak '{taak}' toegevoegd aan de planning!")
                st.rerun()

    # Koppeling met verbouwing
    st.markdown("---")
    sec_div("Budget-koppeling per Categorie", "💰")
    st.caption("Openstaande budgetten uit de verbouwing — gebruik dit als basis voor nieuwe taken.")

    try:
        ynab = calc_ynab_envelopes()
        for env in sorted(ynab["envelopes"], key=lambda x: -x["begroot"]):
            if env["begroot"] > 0:
                pct = min(env["pct"], 100)
                bar = "grn" if pct < 80 else "warn" if pct < 100 else "red"
                n_taken = sum(1 for p in planning if p["Categorie"] == env["naam"])
                st.markdown(f"""
                <div style='display:flex;align-items:center;gap:8px;
                             padding:5px 0;border-bottom:1px solid #F3F4F6;font-size:.78rem;'>
                  <span style='min-width:180px;font-weight:600;color:#374151;'>
                    {'🔨' if env['type']=='verbouwing' else '🛋️'} {env['naam']}</span>
                  <span style='color:#6B7280;min-width:80px;'>€ {env['beschikbaar']:,.0f} vrij</span>
                  <div style='flex:1;background:#F3F4F6;border-radius:999px;height:5px;min-width:60px;'>
                    <div style='width:{pct:.0f}%;height:100%;border-radius:999px;
                                background:{"#10B981" if bar=="grn" else "#F59E0B" if bar=="warn" else "#EF4444"};'></div>
                  </div>
                  <span style='color:#9CA3AF;font-size:.68rem;min-width:60px;text-align:right;'>
                    {n_taken} taken</span>
                </div>""", unsafe_allow_html=True)
    except Exception:
        alert("Budget-koppeling niet beschikbaar.", "warn")


# ══════════════════════════════════════════════════════════════════════════════
# TAB 5: BULK EDITOR
# ══════════════════════════════════════════════════════════════════════════════
with tabs[4]:
    sec_div("Bulk Editor — Alle taken aanpassen", "📝")
    st.caption("Pas meerdere taken tegelijk aan. Klik 'Opslaan' om alle wijzigingen door te voeren.")

    if not planning:
        alert("Geen planningsstappen.", "warn")
    else:
        df_edit = pd.DataFrame(planning)
        show_cols = ["Volgorde","Taak","Categorie","Verantwoordelijke",
                     "Startdatum","Deadline","Status","Prioriteit","Afhankelijk_Van","Notities"]
        for col in show_cols:
            if col not in df_edit.columns:
                df_edit[col] = ""
        df_edit = df_edit[show_cols]

        edited = st.data_editor(
            df_edit,
            column_config={
                "Volgorde":          st.column_config.NumberColumn("Nr.", min_value=1, disabled=True),
                "Taak":              st.column_config.TextColumn("Taak", width="large"),
                "Categorie":         st.column_config.SelectboxColumn(
                    "Categorie", options=VERB_CATS + INBOEDEL_CATS + ["Overig"], width="medium"),
                "Verantwoordelijke": st.column_config.TextColumn("Verant.", width="medium"),
                "Startdatum":        st.column_config.TextColumn("Start"),
                "Deadline":          st.column_config.TextColumn("Deadline"),
                "Status":            st.column_config.SelectboxColumn("Status", options=STATUSSEN),
                "Prioriteit":        st.column_config.SelectboxColumn("Prio", options=PRIORITEITEN),
                "Afhankelijk_Van":   st.column_config.TextColumn("Afhankelijk van"),
                "Notities":          st.column_config.TextColumn("Notities"),
            },
            num_rows="dynamic",
            use_container_width=True,
            height=480,
            key="bulk_plan_editor",
        )

        # Stats na bewerken
        gereed_n = sum(1 for _, r in edited.iterrows() if r.get("Status") == "Gereed")
        pct_done = gereed_n / len(edited) * 100 if len(edited) > 0 else 0
        st.metric("Voortgang na wijzigingen",
                  f"{gereed_n}/{len(edited)} gereed ({pct_done:.0f}%)")

        if st.button("💾 Opslaan naar Excel", type="primary",
                     use_container_width=True, key="save_bulk_plan"):
            new_planning = edited.to_dict(orient="records")
            # Zorg dat Budget_Ref correct is
            for p in new_planning:
                if not p.get("Budget_Ref"):
                    p["Budget_Ref"] = p.get("Categorie", "")
            save_planning(new_planning)
            st.success("✅ Planning opgeslagen naar Excel (backup gemaakt)!")
            st.rerun()
