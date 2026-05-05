"""
utils/kamer_engine.py
Generieke kamer-pagina engine.
Elke kamer-pagina roept `render_kamer_page(kamer)` aan.
Bevat alle 5 tabs: Overzicht, Budget, Taken & Planning, Kosten & AI, Wensen.
"""
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import datetime
import json
import base64

from utils.config import (
    KAMER_EMOJIS, TASK_STATUSES, WISH_STATUSES, PRIORITEITEN,
    BUDGET_CATEGORIES, EENHEDEN, PLOTLY_COLORS, STATUS_EMOJI,
)
from utils.state_manager import (
    get_taken, save_taken, get_kosten, save_kosten,
    get_wensen, save_wensen, get_verbouwing_voor_kamer,
    save_verbouwing_voor_kamer, get_kamer_budget, update_kamer_budget,
    add_bon, get_bonnen,
)
from utils.calculations import calculate_kamer_summary, recalc_verbouwing_totalen
from utils.layout import render_kpi, render_progress, status_badge


# ────────────────────────────────────────────────────────────────────────────
# Hoofdfunctie
# ────────────────────────────────────────────────────────────────────────────

def render_kamer_page(kamer: str) -> None:
    emoji = KAMER_EMOJIS.get(kamer, "🏗️")
    summary = calculate_kamer_summary(kamer)

    tabs = st.tabs([
        "📊 Overzicht",
        "💰 Budget",
        "✅ Taken & Planning",
        "🧾 Kosten & AI",
        "✨ Wensen",
    ])

    with tabs[0]:
        _tab_overzicht(kamer, emoji, summary)
    with tabs[1]:
        _tab_budget(kamer, summary)
    with tabs[2]:
        _tab_taken(kamer)
    with tabs[3]:
        _tab_kosten(kamer)
    with tabs[4]:
        _tab_wensen(kamer)


# ────────────────────────────────────────────────────────────────────────────
# TAB 1: Overzicht
# ────────────────────────────────────────────────────────────────────────────

def _tab_overzicht(kamer: str, emoji: str, summary: dict) -> None:
    st.markdown(f"### {emoji} {kamer} — Samenvatting")

    # KPI rij
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        render_kpi("💰 Budget",     f"€ {summary['toegewezen']:,.0f}")
    with c2:
        render_kpi("🔨 Besteed",   f"€ {summary['besteed']:,.0f}",
                   variant="warning" if summary["pct_budget"] > 70 else "")
    with c3:
        variant = "danger" if summary["beschikbaar"] < 0 else "success"
        render_kpi("🎯 Resterend", f"€ {summary['beschikbaar']:,.0f}", variant=variant)
    with c4:
        render_kpi("✅ Taken",      f"{summary['n_gereed']}/{summary['n_taken']}",
                   delta=f"{summary['pct_taken']:.0f}% gereed")

    st.markdown("<br>", unsafe_allow_html=True)

    # Voortgangsbalken
    render_progress("💰 Budget uitnutting", summary["pct_budget"])
    render_progress("✅ Taken gereed",       summary["pct_taken"])

    st.markdown("---")

    # Taken statusverdeling — donut chart
    col_left, col_right = st.columns(2)

    with col_left:
        st.markdown("**📋 Taken Status**")
        taken = get_taken(kamer)
        if taken:
            counts = {"Todo": summary["n_todo"], "Bezig": summary["n_bezig"], "Gereed": summary["n_gereed"]}
            fig = go.Figure(go.Pie(
                labels=list(counts.keys()),
                values=list(counts.values()),
                hole=0.6,
                marker_colors=["#6B7280", "#F59E0B", "#10B981"],
            ))
            fig.update_layout(
                showlegend=True,
                margin=dict(l=0, r=0, t=10, b=0),
                height=220,
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Geen taken aangemaakt.")

    with col_right:
        st.markdown("**🏠 Kosten verdeling**")
        kosten = get_kosten(kamer)
        if kosten:
            cat_sum: dict = {}
            for k in kosten:
                c = k.get("Categorie", "Overig") or "Overig"
                cat_sum[c] = cat_sum.get(c, 0) + float(k.get("Bedrag (€)", 0) or 0)
            fig2 = go.Figure(go.Pie(
                labels=list(cat_sum.keys()),
                values=list(cat_sum.values()),
                hole=0.6,
                marker_colors=PLOTLY_COLORS,
                textinfo="label+percent",
            ))
            fig2.update_layout(
                showlegend=False,
                margin=dict(l=0, r=0, t=10, b=0),
                height=220,
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
            )
            st.plotly_chart(fig2, use_container_width=True)
        else:
            st.info("Geen kosten geregistreerd.")

    # Wensen samenvatting
    wensen = get_wensen(kamer)
    if wensen:
        st.markdown("---")
        st.markdown("**✨ Wensen samenvatting**")
        for status in WISH_STATUSES:
            items = [w for w in wensen if w.get("Status") == status]
            if items:
                st.markdown(f"{STATUS_EMOJI.get(status, '')} **{status}** ({len(items)})")


# ────────────────────────────────────────────────────────────────────────────
# TAB 2: Budget
# ────────────────────────────────────────────────────────────────────────────

def _tab_budget(kamer: str, summary: dict) -> None:
    st.markdown("### 💰 Budget & Verbouwingsbegroting")

    # Toegewezen budget aanpassen
    bud = get_kamer_budget(kamer)
    st.markdown("#### 🏦 Toegewezen Budget")
    new_budget = st.number_input(
        f"Budget voor {kamer} (€)",
        min_value=0.0, step=500.0,
        value=float(bud["Toegewezen Budget (€)"]),
        format="%.2f",
        key=f"budget_input_{kamer}",
    )
    if st.button("💾 Budget opslaan", key=f"save_budget_{kamer}", type="primary"):
        update_kamer_budget(kamer, new_budget)
        st.success(f"✅ Budget voor {kamer} bijgewerkt naar € {new_budget:,.2f}")
        st.rerun()

    st.markdown("---")

    # Verbouwing begroting editor
    st.markdown("#### 🧱 Verbouwingsbegroting")
    st.caption("Wijzig hoeveelheden en kosten; 'Totaal (€)' wordt automatisch herberekend bij opslaan.")

    verb_df = get_verbouwing_voor_kamer(kamer)

    if verb_df.empty:
        st.info("Nog geen begroting-posten voor deze kamer. Voeg er hieronder toe.")
        verb_df = pd.DataFrame(columns=[
            "Categorie", "Post", "Aantal", "Eenheid",
            "Kosten per eenheid (€)", "Totaal (€)", "Opmerking",
        ])

    # Verwijder Kamer-kolom uit editor (wordt automatisch beheerd)
    edit_cols = ["Categorie", "Post", "Aantal", "Eenheid", "Kosten per eenheid (€)", "Totaal (€)", "Opmerking"]
    for col in edit_cols:
        if col not in verb_df.columns:
            verb_df[col] = "" if col in ["Categorie", "Post", "Eenheid", "Opmerking"] else 0.0

    edited = st.data_editor(
        verb_df[edit_cols],
        column_config={
            "Categorie":             st.column_config.SelectboxColumn("Categorie", options=BUDGET_CATEGORIES),
            "Post":                  st.column_config.TextColumn("Post", width="medium"),
            "Aantal":                st.column_config.NumberColumn("Aantal", min_value=0, step=1, format="%.1f"),
            "Eenheid":               st.column_config.SelectboxColumn("Eenheid", options=EENHEDEN),
            "Kosten per eenheid (€)": st.column_config.NumberColumn("Kosten/eenheid", format="€ %.2f", min_value=0),
            "Totaal (€)":            st.column_config.NumberColumn("Totaal", format="€ %.2f", disabled=True),
            "Opmerking":             st.column_config.TextColumn("Opmerking", width="medium"),
        },
        num_rows="dynamic",
        use_container_width=True,
        key=f"editor_verb_{kamer}",
    )

    if st.button("💾 Begroting opslaan", key=f"save_verb_{kamer}", type="primary"):
        edited = recalc_verbouwing_totalen(edited)
        save_verbouwing_voor_kamer(kamer, edited)
        from utils.state_manager import _recalc_gerealiseerd
        _recalc_gerealiseerd(kamer)
        st.success("✅ Verbouwingsbegroting opgeslagen!")
        st.rerun()

    # Totaaltelling
    if not edited.empty and "Totaal (€)" in edited.columns:
        recalced = recalc_verbouwing_totalen(edited)
        totaal = float(recalced["Totaal (€)"].sum())
        st.metric("Totaal verbouwingsbegroting", f"€ {totaal:,.2f}")


# ────────────────────────────────────────────────────────────────────────────
# TAB 3: Taken & Planning
# ────────────────────────────────────────────────────────────────────────────

def _tab_taken(kamer: str) -> None:
    st.markdown("### ✅ Taken & Planning")

    taken = get_taken(kamer)

    # Nieuwe taak toevoegen
    with st.expander("➕ Nieuwe taak toevoegen", expanded=False):
        t_col1, t_col2 = st.columns(2)
        with t_col1:
            t_naam = st.text_input("Taakomschrijving", key=f"t_naam_{kamer}")
            t_verant = st.text_input("Verantwoordelijke", key=f"t_verant_{kamer}")
        with t_col2:
            t_deadline = st.date_input("Deadline", key=f"t_date_{kamer}")
            t_opmerking = st.text_area("Opmerking", height=80, key=f"t_opm_{kamer}")

        if st.button("➕ Taak toevoegen", key=f"add_taak_{kamer}", type="primary"):
            if t_naam.strip():
                taken.append({
                    "Taak": t_naam.strip(),
                    "Status": "Todo",
                    "Verantwoordelijke": t_verant,
                    "Deadline": str(t_deadline),
                    "Opmerking": t_opmerking,
                    "Kamer": kamer,
                })
                save_taken(kamer, taken)
                st.success(f"✅ Taak '{t_naam}' toegevoegd!")
                st.rerun()
            else:
                st.warning("Voer een taakomschrijving in.")

    st.markdown("---")

    # Kanban-stijl weergave
    if not taken:
        st.info("Nog geen taken. Voeg er hierboven toe.")
        return

    cols_kanban = st.columns(3)
    headers = {"Todo": "⚪ To Do", "Bezig": "🟡 Bezig", "Gereed": "🟢 Gereed"}
    col_map  = {"Todo": cols_kanban[0], "Bezig": cols_kanban[1], "Gereed": cols_kanban[2]}

    for status, col in col_map.items():
        status_taken = [(i, t) for i, t in enumerate(taken) if t.get("Status") == status]
        with col:
            st.markdown(f"**{headers[status]}** ({len(status_taken)})")
            for idx, taak in status_taken:
                with st.container():
                    st.markdown(f"""
                    <div style='background:#F9FAFB; border-radius:10px; padding:12px;
                                border-left:4px solid {"#6B7280" if status=="Todo" else "#F59E0B" if status=="Bezig" else "#10B981"};
                                margin-bottom:10px;'>
                      <div style='font-weight:600; color:#1A1A2E; font-size:0.9rem;'>{taak.get("Taak","")}</div>
                      <div style='font-size:0.75rem; color:#6B7280; margin-top:4px;'>
                        👤 {taak.get("Verantwoordelijke","—")} &nbsp;|&nbsp;
                        📅 {taak.get("Deadline","—")}
                      </div>
                      {f'<div style="font-size:0.75rem; color:#374151; margin-top:4px;">💬 {taak.get("Opmerking","")}</div>' if taak.get("Opmerking") else ""}
                    </div>
                    """, unsafe_allow_html=True)

                    # Status wijzig knoppen
                    btn_cols = st.columns(len(TASK_STATUSES))
                    for bi, new_st in enumerate(TASK_STATUSES):
                        if new_st != status:
                            if btn_cols[bi].button(
                                f"→ {new_st}", key=f"st_{kamer}_{idx}_{new_st}",
                                use_container_width=True,
                            ):
                                taken[idx]["Status"] = new_st
                                save_taken(kamer, taken)
                                st.rerun()

                    if st.button("🗑️ Verwijder", key=f"del_taak_{kamer}_{idx}",
                                 use_container_width=True):
                        taken.pop(idx)
                        save_taken(kamer, taken)
                        st.rerun()

    st.markdown("---")

    # Bulk editor
    with st.expander("📝 Bulk taken editor", expanded=False):
        taken_df = pd.DataFrame(taken)
        if not taken_df.empty:
            edited_taken = st.data_editor(
                taken_df[["Taak", "Status", "Verantwoordelijke", "Deadline", "Opmerking"]],
                column_config={
                    "Taak":              st.column_config.TextColumn("Taak", width="large"),
                    "Status":            st.column_config.SelectboxColumn("Status", options=TASK_STATUSES),
                    "Verantwoordelijke": st.column_config.TextColumn("Verantwoordelijke"),
                    "Deadline":          st.column_config.TextColumn("Deadline"),
                    "Opmerking":         st.column_config.TextColumn("Opmerking"),
                },
                num_rows="dynamic",
                use_container_width=True,
                key=f"bulk_taken_{kamer}",
            )
            if st.button("💾 Bulk opslaan", key=f"save_bulk_taken_{kamer}", type="primary"):
                new_taken = edited_taken.to_dict(orient="records")
                for t in new_taken:
                    t["Kamer"] = kamer
                save_taken(kamer, new_taken)
                st.success("✅ Taken opgeslagen!")
                st.rerun()


# ────────────────────────────────────────────────────────────────────────────
# TAB 4: Kosten & AI
# ────────────────────────────────────────────────────────────────────────────

def _tab_kosten(kamer: str) -> None:
    st.markdown("### 🧾 Kosten & AI Bon Scanner")

    kosten = get_kosten(kamer)

    # Totalen
    totaal_kosten = sum(float(k.get("Bedrag (€)", 0) or 0) for k in kosten)
    col_tot1, col_tot2 = st.columns(2)
    col_tot1.metric("Totaal uitgaven", f"€ {totaal_kosten:,.2f}")
    col_tot2.metric("Aantal bonnen",   str(len(kosten)))

    st.markdown("---")

    # Kosten toevoegen
    st.markdown("#### ➕ Nieuwe kostenpost registreren")
    with st.form(f"kosten_form_{kamer}", clear_on_submit=True):
        k1, k2 = st.columns(2)
        with k1:
            k_datum      = st.date_input("Datum", value=datetime.date.today())
            k_leverancier = st.text_input("Leverancier")
            k_bedrag     = st.number_input("Bedrag (€)", min_value=0.0, step=0.01, format="%.2f")
        with k2:
            k_categorie  = st.selectbox("Categorie", BUDGET_CATEGORIES)
            k_omschrijving = st.text_area("Omschrijving", height=100)

        submitted = st.form_submit_button("➕ Kosten toevoegen", type="primary", use_container_width=True)
        if submitted:
            if k_leverancier.strip() and k_bedrag > 0:
                kosten.append({
                    "Datum": str(k_datum), "Leverancier": k_leverancier,
                    "Bedrag (€)": k_bedrag, "Categorie": k_categorie,
                    "Omschrijving": k_omschrijving, "Kamer": kamer,
                })
                save_kosten(kamer, kosten)
                from utils.state_manager import _recalc_gerealiseerd
                _recalc_gerealiseerd(kamer)
                st.success(f"✅ € {k_bedrag:.2f} van {k_leverancier} toegevoegd!")
                st.rerun()
            else:
                st.warning("Vul leverancier en bedrag in.")

    st.markdown("---")

    # 🤖 AI Bon Scanner
    st.markdown("#### 🤖 Gemini AI Bon Scanner")
    st.markdown("""
    <div class='bon-card'>
      <h3>📸 Upload een kassabon</h3>
      <p style='color:#9CA3AF; font-size:0.9rem;'>
        De AI extraheert automatisch leverancier, datum, bedrag en categorie.
        Vereist een Gemini API-sleutel in <code>.streamlit/secrets.toml</code>.
      </p>
    </div>
    """, unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)

    uploaded_bon = st.file_uploader(
        "Upload bon (JPG/PNG/PDF)",
        type=["jpg", "jpeg", "png", "pdf"],
        key=f"bon_upload_{kamer}",
    )

    if uploaded_bon:
        st.image(uploaded_bon, caption="Geüploade bon", width=300)
        if st.button("🤖 Analyseer met AI", key=f"analyze_bon_{kamer}", type="primary"):
            _analyze_bon_with_ai(uploaded_bon, kamer)

    st.markdown("---")

    # Bestaande kosten tabel
    if kosten:
        st.markdown("#### 📋 Geregistreerde Kosten")
        df_kosten = pd.DataFrame(kosten)
        display_cols = [c for c in ["Datum", "Leverancier", "Bedrag (€)", "Categorie", "Omschrijving"] if c in df_kosten.columns]

        edited_kosten = st.data_editor(
            df_kosten[display_cols],
            column_config={
                "Bedrag (€)":  st.column_config.NumberColumn("Bedrag (€)", format="€ %.2f"),
                "Datum":       st.column_config.TextColumn("Datum"),
                "Leverancier": st.column_config.TextColumn("Leverancier"),
                "Categorie":   st.column_config.SelectboxColumn("Categorie", options=BUDGET_CATEGORIES),
                "Omschrijving": st.column_config.TextColumn("Omschrijving"),
            },
            num_rows="dynamic",
            use_container_width=True,
            key=f"kosten_editor_{kamer}",
        )
        if st.button("💾 Kosten opslaan", key=f"save_kosten_{kamer}", type="primary"):
            new_kosten = edited_kosten.to_dict(orient="records")
            for k in new_kosten:
                k["Kamer"] = kamer
            save_kosten(kamer, new_kosten)
            from utils.state_manager import _recalc_gerealiseerd
            _recalc_gerealiseerd(kamer)
            st.success("✅ Kosten opgeslagen!")
            st.rerun()

        # Timeline chart
        if any(k.get("Datum") for k in kosten):
            from utils.calculations import calculate_kosten_timeline
            timeline = calculate_kosten_timeline()
            kamer_timeline = timeline[timeline["Kamer"] == kamer]
            if not kamer_timeline.empty:
                fig = px.bar(
                    kamer_timeline, x="Datum", y="Bedrag (€)",
                    color="Categorie", title="Kosten in de tijd",
                    color_discrete_sequence=PLOTLY_COLORS,
                )
                fig.update_layout(
                    plot_bgcolor="rgba(0,0,0,0)",
                    paper_bgcolor="rgba(0,0,0,0)",
                    height=250,
                    margin=dict(l=0, r=0, t=30, b=0),
                )
                st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Geen kosten geregistreerd voor deze kamer.")


def _analyze_bon_with_ai(uploaded_file, kamer: str) -> None:
    """Analyseer een bon-foto met Gemini 2.5 Flash."""
    try:
        import google.generativeai as genai
        api_key = st.secrets.get("GEMINI_API_KEY", "")
        if not api_key:
            st.warning("⚠️ Geen Gemini API-sleutel gevonden. Voeg `GEMINI_API_KEY` toe aan `.streamlit/secrets.toml`.")
            return

        genai.configure(api_key=api_key)
        model = genai.GenerativeModel("gemini-2.5-flash")

        # Lees bestand als bytes
        img_bytes = uploaded_file.read()
        img_b64   = base64.b64encode(img_bytes).decode("utf-8")
        mime_type = uploaded_file.type or "image/jpeg"

        prompt = """
        Analyseer deze kassabon en extraheer de volgende informatie in JSON:
        {
          "Datum": "YYYY-MM-DD",
          "Leverancier": "naam van de winkel",
          "Bedrag (€)": 0.00,
          "BTW (€)": 0.00,
          "Categorie": "een van: Materialen, Arbeid, Keuken, Sanitair, Tegels, Verlichting, Vloer, Schilderwerk, Overig",
          "Omschrijving": "korte samenvatting van aankoop"
        }
        Retourneer ALLEEN de JSON, geen verdere tekst.
        """

        response = model.generate_content([
            {"mime_type": mime_type, "data": img_b64},
            prompt,
        ])

        raw = response.text.strip().strip("```json").strip("```").strip()
        bon_data = json.loads(raw)

        st.success("✅ Bon geanalyseerd!")
        st.json(bon_data)

        bon_data["Kamer"] = kamer
        if st.button("💾 Bon opslaan als kostenpost", key=f"save_bon_{kamer}_{uploaded_file.name}"):
            kosten = get_kosten(kamer)
            kosten.append({
                "Datum":       bon_data.get("Datum", ""),
                "Leverancier": bon_data.get("Leverancier", ""),
                "Bedrag (€)":  float(bon_data.get("Bedrag (€)", 0)),
                "Categorie":   bon_data.get("Categorie", "Overig"),
                "Omschrijving": bon_data.get("Omschrijving", ""),
                "Kamer":       kamer,
            })
            save_kosten(kamer, kosten)
            add_bon(bon_data)
            from utils.state_manager import _recalc_gerealiseerd
            _recalc_gerealiseerd(kamer)
            st.success("✅ Bon opgeslagen als kostenpost!")
            st.rerun()

    except ImportError:
        st.error("Google Generative AI library niet geïnstalleerd. Voer uit: `pip install google-generativeai`")
    except json.JSONDecodeError as e:
        st.error(f"Kon JSON niet parsen: {e}")
    except Exception as e:
        st.error(f"AI analyse mislukt: {e}")


# ────────────────────────────────────────────────────────────────────────────
# TAB 5: Wensen
# ────────────────────────────────────────────────────────────────────────────

def _tab_wensen(kamer: str) -> None:
    st.markdown("### ✨ Wensen & Verlanglijst")

    wensen = get_wensen(kamer)
    totaal_geschat = sum(float(w.get("Geschat Bedrag (€)", 0) or 0) for w in wensen)
    gear_wensen    = [w for w in wensen if w.get("Status") == "Gerealiseerd"]

    c1, c2, c3 = st.columns(3)
    c1.metric("Totaal wensen",        str(len(wensen)))
    c2.metric("Gerealiseerd",         str(len(gear_wensen)))
    c3.metric("Geschat totaalbedrag", f"€ {totaal_geschat:,.0f}")

    st.markdown("---")

    # Nieuwe wens toevoegen
    with st.expander("➕ Nieuwe wens toevoegen", expanded=False):
        w1, w2 = st.columns(2)
        with w1:
            w_naam    = st.text_input("Wens omschrijving", key=f"w_naam_{kamer}")
            w_status  = st.selectbox("Status", WISH_STATUSES, key=f"w_status_{kamer}")
        with w2:
            w_prior   = st.selectbox("Prioriteit", PRIORITEITEN, index=1, key=f"w_prior_{kamer}")
            w_bedrag  = st.number_input("Geschat bedrag (€)", min_value=0.0, step=50.0, key=f"w_bedrag_{kamer}")
            w_opm     = st.text_input("Opmerking", key=f"w_opm_{kamer}")

        if st.button("✨ Wens toevoegen", key=f"add_wens_{kamer}", type="primary"):
            if w_naam.strip():
                wensen.append({
                    "Wens": w_naam.strip(), "Status": w_status,
                    "Prioriteit": w_prior, "Geschat Bedrag (€)": w_bedrag,
                    "Opmerking": w_opm, "Kamer": kamer,
                })
                save_wensen(kamer, wensen)
                st.success(f"✅ Wens '{w_naam}' toegevoegd!")
                st.rerun()
            else:
                st.warning("Voer een wens in.")

    st.markdown("---")

    if not wensen:
        st.info("Nog geen wensen geregistreerd.")
        return

    # Weergave per status
    for status in WISH_STATUSES:
        status_wensen = [(i, w) for i, w in enumerate(wensen) if w.get("Status") == status]
        if not status_wensen:
            continue
        emoji = {"Idee": "💡", "Gepland": "📋", "Gerealiseerd": "✅"}.get(status, "")
        st.markdown(f"#### {emoji} {status} ({len(status_wensen)})")
        for idx, wens in status_wensen:
            with st.container():
                prio_col = {"Laag": "#10B981", "Middel": "#F59E0B", "Hoog": "#EF4444"}.get(wens.get("Prioriteit", "Middel"), "#6B7280")
                bedrag   = float(wens.get("Geschat Bedrag (€)", 0) or 0)
                st.markdown(f"""
                <div style='background:#FFFFFF; border-radius:12px; padding:14px 18px;
                            border-left:4px solid {prio_col}; margin-bottom:8px;
                            box-shadow:0 2px 8px rgba(0,0,0,0.06);'>
                  <div style='display:flex; justify-content:space-between; align-items:flex-start;'>
                    <div>
                      <div style='font-weight:700; font-size:0.95rem; color:#1A1A2E;'>{wens.get("Wens","")}</div>
                      <div style='font-size:0.78rem; color:#6B7280; margin-top:3px;'>
                        🔥 {wens.get("Prioriteit","—")} &nbsp;|&nbsp;
                        💰 € {bedrag:,.0f} geschat
                        {f' &nbsp;|&nbsp; 💬 {wens.get("Opmerking","")}' if wens.get("Opmerking") else ""}
                      </div>
                    </div>
                  </div>
                </div>
                """, unsafe_allow_html=True)

                btn_cols = st.columns(len(WISH_STATUSES) + 1)
                for bi, new_st in enumerate(WISH_STATUSES):
                    if new_st != status:
                        if btn_cols[bi].button(f"→ {new_st}", key=f"wst_{kamer}_{idx}_{new_st}"):
                            wensen[idx]["Status"] = new_st
                            save_wensen(kamer, wensen)
                            st.rerun()
                if btn_cols[-1].button("🗑️", key=f"del_wens_{kamer}_{idx}"):
                    wensen.pop(idx)
                    save_wensen(kamer, wensen)
                    st.rerun()

    st.markdown("---")

    # Bulk editor
    with st.expander("📝 Bulk wensen editor", expanded=False):
        wensen_df = pd.DataFrame(wensen)
        if not wensen_df.empty:
            edit_cols = [c for c in ["Wens", "Status", "Prioriteit", "Geschat Bedrag (€)", "Opmerking"] if c in wensen_df.columns]
            edited_wensen = st.data_editor(
                wensen_df[edit_cols],
                column_config={
                    "Wens":               st.column_config.TextColumn("Wens", width="large"),
                    "Status":             st.column_config.SelectboxColumn("Status", options=WISH_STATUSES),
                    "Prioriteit":         st.column_config.SelectboxColumn("Prioriteit", options=PRIORITEITEN),
                    "Geschat Bedrag (€)": st.column_config.NumberColumn("Geschat Bedrag (€)", format="€ %.0f"),
                    "Opmerking":          st.column_config.TextColumn("Opmerking"),
                },
                num_rows="dynamic",
                use_container_width=True,
                key=f"bulk_wensen_{kamer}",
            )
            if st.button("💾 Bulk opslaan", key=f"save_bulk_wensen_{kamer}", type="primary"):
                new_wensen = edited_wensen.to_dict(orient="records")
                for w in new_wensen:
                    w["Kamer"] = kamer
                save_wensen(kamer, new_wensen)
                st.success("✅ Wensen opgeslagen!")
                st.rerun()
