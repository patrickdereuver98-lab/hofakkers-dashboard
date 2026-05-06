"""
pages/1_Verbouwing.py  –  Hofakkers 44  v3.0
"""
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px

from utils.ui import (
    page_setup, header, kpi, progress, sidebar,
    render_room_card, render_ynab_row, ynab_transfer_form, alert, sec_div,
)
from utils.notifications import render_notification_bar
from utils.state import (
    init, calc_maand_totalen, calc_project,
    calc_verbouwing_totalen, calc_ynab_envelopes, calc_budget_vs_actuals,
    verbouwing, set_verbouwing,
    get_kosten_df, set_kosten_df,
)
from utils.config import CHART_COLORS, VERB_CATS, EENHEDEN, FISCAAL_TYPES
from utils.excel_handler import save_verbouwing, save_kosten

page_setup("🔨 Verbouwing – Hofakkers 44")
init()

sidebar(calc_maand_totalen(), calc_project())
header("🔨 Verbouwingsbegroting", "HomeZada · YNAB · Fiscaal-bewust", "🔨")

# Proactieve notificaties (budget-overschrijdingen, deadlines)
render_notification_bar(max_visible=2, filter_page="Verbouwing")

verb_info = calc_verbouwing_totalen()
totaal    = verb_info["totaal"]
cats      = verb_info["categorieën"]
ynab      = calc_ynab_envelopes()

# ── KPI rij ─────────────────────────────────────────────────────────────────
c1, c2, c3, c4 = st.columns(4)
with c1: kpi("💰 Totaal Begroot", f"€ {totaal:,.0f}", "verbouwing")
with c2:
    biggest = max(cats, key=cats.get) if cats else "—"
    kpi("🏆 Grootste Post", biggest, f"€ {cats.get(biggest,0):,.0f}")
with c3: kpi("📋 Aantal Posten", str(len(verbouwing())), "begrotingsregels")
with c4:
    bva  = calc_budget_vs_actuals()
    real = bva[bva["Type"]=="Verbouwing"]["Gerealiseerd (€)"].sum() if not bva.empty else 0
    rest = totaal - real
    kpi("🎯 Beschikbaar", f"€ {rest:,.0f}",
        "✓ on track" if rest >= 0 else "⚠️ over budget",
        "grn" if rest >= 0 else "red")

st.markdown("---")

tabs = st.tabs([
    "🏘️ Kamer Gallery",
    "📊 Budget vs Actuals",
    "📬 YNAB Envelopes",
    "🔄 Verschuif Geld",
    "✏️ Begroting Bewerken",
    "🧾 Uitgaven Registreren",
    "📈 Analyse",
])

# ── Tab 1: Notion Gallery ──────────────────────────────────────────────────
with tabs[0]:
    sec_div("Kamer- & Categorieoverzicht", "🏘️")
    if cats:
        cats_list = sorted(cats.items(), key=lambda x: -x[1])
        cols = st.columns(3)
        verb_envs = {e["naam"]: e for e in ynab["envelopes"] if e["type"] == "verbouwing"}
        df_v = verbouwing()

        for i, (cat, begroot) in enumerate(cats_list):
            env  = verb_envs.get(cat, {})
            real = env.get("gerealiseerd", 0.0)
            override = env.get("override", 0)
            n    = int(df_v[df_v["Categorie"] == cat].shape[0]) if not df_v.empty else 0
            extra = ""
            if override != 0:
                sign = "+" if override > 0 else ""
                extra = f"⚙️ override {sign}€{override:,.0f}"
            with cols[i % 3]:
                render_room_card(naam=cat, begroot=begroot,
                                 gerealiseerd=real, n_posten=n,
                                 extra_caption=extra)
    else:
        alert("Geen verbouwingsdata beschikbaar.", "warn")

# ── Tab 2: HomeZada Budget vs Actuals ──────────────────────────────────────
with tabs[1]:
    sec_div("Budget vs Gerealiseerd", "📊")
    bva = calc_budget_vs_actuals()
    verb_bva = bva[bva["Type"] == "Verbouwing"] if not bva.empty else bva

    if not verb_bva.empty:
        def _kleur(val):
            if isinstance(val,(int,float)):
                return "color:#10B981;font-weight:600" if val>0 else \
                       "color:#EF4444;font-weight:600" if val<0 else ""
            return ""
        st.dataframe(
            verb_bva.style
                .format({"Begroot (€)":"€ {:,.0f}","Gerealiseerd (€)":"€ {:,.0f}",
                         "Verschil (€)":"€ {:,.0f}","% Gebruikt":"{:.1f}%"})
                .map(_kleur, subset=["Verschil (€)"])
                .background_gradient(subset=["% Gebruikt"], cmap="RdYlGn_r", vmin=0, vmax=110),
            use_container_width=True, hide_index=True,
        )

        fig = go.Figure()
        fig.add_trace(go.Bar(name="Begroot", x=verb_bva["Categorie"],
                             y=verb_bva["Begroot (€)"], marker_color=CHART_COLORS[0],
                             text=verb_bva["Begroot (€)"].apply(lambda x: f"€{x:,.0f}"),
                             textposition="outside"))
        fig.add_trace(go.Bar(name="Gerealiseerd", x=verb_bva["Categorie"],
                             y=verb_bva["Gerealiseerd (€)"], marker_color=CHART_COLORS[1],
                             text=verb_bva["Gerealiseerd (€)"].apply(lambda x: f"€{x:,.0f}"),
                             textposition="outside"))
        fig.update_layout(
            barmode="group", plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
            yaxis=dict(tickprefix="€"), legend=dict(orientation="h",y=-0.25),
            margin=dict(l=0,r=0,t=10,b=60), height=340,
        )
        st.plotly_chart(fig, use_container_width=True)

        st.markdown("##### Voortgang per Categorie")
        for _, row in verb_bva.iterrows():
            pct = float(row["% Gebruikt"])
            progress(f"{row['Categorie']}  (€ {row['Gerealiseerd (€)']:,.0f} / € {row['Begroot (€)']:,.0f})", pct)
    else:
        alert("Nog geen uitgaven geregistreerd. Gebruik tab 'Uitgaven Registreren'.", "blu")

# ── Tab 3: YNAB Envelopes ──────────────────────────────────────────────────
with tabs[2]:
    sec_div("YNAB Envelopes", "📬")
    verb_envs_list = [e for e in ynab["envelopes"] if e["type"] == "verbouwing"]
    if verb_envs_list:
        totaal_b = sum(e["begroot"] for e in verb_envs_list)
        totaal_r = sum(e["gerealiseerd"] for e in verb_envs_list)
        avail    = totaal_b - totaal_r
        ec1, ec2, ec3 = st.columns(3)
        ec1.metric("Totaal Begroot",      f"€ {totaal_b:,.0f}")
        ec2.metric("Totaal Gerealiseerd", f"€ {totaal_r:,.0f}")
        ec3.metric("Totaal Beschikbaar",  f"€ {avail:,.0f}",
                   delta_color="normal" if avail >= 0 else "inverse")
        st.markdown("")
        for e in verb_envs_list:
            render_ynab_row(e)
    else:
        alert("Geen verbouwingsenvelopes beschikbaar.", "warn")

# ── Tab 4: Verschuif geld (YNAB transfer) ──────────────────────────────────
with tabs[3]:
    sec_div("Verschuif geld tussen envelopes", "🔄")
    ynab_transfer_form(
        envelopes=ynab["envelopes"],
        vrije_buffer=ynab["vrij"],
        key_prefix="verb_ynab",
    )

# ── Tab 5: Begroting Bewerken ──────────────────────────────────────────────
with tabs[4]:
    sec_div("Verbouwingsbegroting bewerken", "✏️")
    st.caption("Totaal (€) wordt automatisch herberekend op basis van Aantal × Kosten/eenheid.")

    df_edit = verbouwing().copy()
    edit_cols = ["Categorie","Post","Aantal","Eenheid","Kosten per eenheid (€)","Totaal (€)","Opmerking"]
    for col in edit_cols:
        if col not in df_edit.columns:
            df_edit[col] = "" if col in ("Categorie","Post","Eenheid","Opmerking") else 0.0
    df_edit = df_edit[edit_cols]

    edited = st.data_editor(
        df_edit,
        column_config={
            "Categorie":              st.column_config.SelectboxColumn("Categorie", options=VERB_CATS, width="medium"),
            "Post":                   st.column_config.TextColumn("Post", width="large"),
            "Aantal":                 st.column_config.NumberColumn("Aantal", min_value=0, step=0.5, format="%.1f"),
            "Eenheid":                st.column_config.SelectboxColumn("Eenheid", options=EENHEDEN),
            "Kosten per eenheid (€)": st.column_config.NumberColumn("Kosten/eenheid", format="€ %.2f", min_value=0),
            "Totaal (€)":             st.column_config.NumberColumn("Totaal", format="€ %.2f", disabled=True),
            "Opmerking":              st.column_config.TextColumn("Opmerking"),
        },
        num_rows="dynamic", use_container_width=True, height=480, key="editor_verbouwing",
    )

    edited = edited.copy()
    edited["Aantal"] = pd.to_numeric(edited["Aantal"], errors="coerce").fillna(0)
    edited["Kosten per eenheid (€)"] = pd.to_numeric(edited["Kosten per eenheid (€)"], errors="coerce").fillna(0)
    edited["Totaal (€)"] = edited["Aantal"] * edited["Kosten per eenheid (€)"]
    nieuw = float(edited["Totaal (€)"].sum())

    st.metric("Nieuw totaal", f"€ {nieuw:,.2f}",
              delta=f"€ {nieuw-totaal:+,.2f} t.o.v. huidige begroting")

    # ── Single save knop ──
    if st.button("💾 Opslaan naar Excel", type="primary",
                 use_container_width=True, key="verb_save"):
        set_verbouwing(edited)
        if save_verbouwing(edited):
            st.success("✅ Opgeslagen naar Excel (backup gemaakt)")
            st.rerun()
        else:
            st.error("❌ Mislukt — is Excel geopend?")

# ── Tab 6: Uitgaven Registreren ───────────────────────────────────────────
with tabs[5]:
    sec_div("Uitgaven Registreren — HomeZada Audit Trail", "🧾")
    st.caption("Koppel elke uitgave aan een categorie en fiscaal type. Cruciaal voor eigenwoningschuld en bewaarplicht (7 jaar).")

    kosten_df = get_kosten_df()

    with st.form("kosten_form_verb", clear_on_submit=True):
        f1, f2, f3 = st.columns(3)
        with f1:
            datum       = st.date_input("Datum")
            leverancier = st.text_input("Leverancier")
        with f2:
            bedrag      = st.number_input("Bedrag (€)", min_value=0.0, step=0.01, format="%.2f")
            categorie   = st.selectbox("Categorie", VERB_CATS)
        with f3:
            fiscaal_type = st.selectbox(
                "Fiscaal Type", FISCAAL_TYPES,
                help="Verbetering = eigenwoningschuld verhogend (Box 1). "
                     "Onderhoud = gewone aftrekpost. Neutraal = geen fiscale impact.",
            )
            post_ref     = st.text_input("Post Referentie", placeholder="bijv. 'Uitbouw casco'")
            omschrijving = st.text_area("Omschrijving", height=68)

        submitted = st.form_submit_button("➕ Uitgave toevoegen", type="primary",
                                          use_container_width=True)
        if submitted:
            if leverancier.strip() and bedrag > 0:
                new_row = {
                    "Datum":         str(datum),
                    "Leverancier":   leverancier.strip(),
                    "Bedrag (€)":    bedrag,
                    "Categorie":     categorie,
                    "Omschrijving":  omschrijving,
                    "Fiscaal_Type":  fiscaal_type,
                    "Post_Ref":      post_ref,
                    "Bon_Ref":       "",
                }
                if kosten_df.empty:
                    kosten_df = pd.DataFrame([new_row])
                else:
                    kosten_df = pd.concat([kosten_df, pd.DataFrame([new_row])],
                                          ignore_index=True)
                set_kosten_df(kosten_df)
                # Direct naar Excel
                if save_kosten(kosten_df):
                    st.success(f"✅ € {bedrag:.2f} van {leverancier} opgeslagen!")
                    st.rerun()
                else:
                    st.warning("⚠️ Toegevoegd in app, maar Excel save mislukt.")
            else:
                st.warning("Vul leverancier en bedrag in.")

    if not kosten_df.empty:
        st.markdown("---")
        st.markdown("**Geregistreerde uitgaven:**")
        totaal_k    = kosten_df["Bedrag (€)"].sum() if "Bedrag (€)" in kosten_df else 0
        verb_kosten = kosten_df[kosten_df["Categorie"].isin(VERB_CATS)]["Bedrag (€)"].sum() \
                      if "Bedrag (€)" in kosten_df and "Categorie" in kosten_df else 0
        tk1, tk2 = st.columns(2)
        tk1.metric("Totaal verbouwingsuitgaven", f"€ {verb_kosten:,.2f}")
        tk2.metric("Totaal alle uitgaven",       f"€ {totaal_k:,.2f}")

        edited_k = st.data_editor(
            kosten_df,
            column_config={
                "Bedrag (€)":   st.column_config.NumberColumn("Bedrag", format="€ %.2f"),
                "Fiscaal_Type": st.column_config.SelectboxColumn("Fiscaal Type", options=FISCAAL_TYPES),
                "Categorie":    st.column_config.SelectboxColumn("Categorie",
                                                                   options=VERB_CATS+["Overig"]),
            },
            num_rows="dynamic", use_container_width=True, height=320,
            key="editor_kosten_verb",
        )
        if st.button("💾 Wijzigingen opslaan", type="primary", key="save_kosten_v"):
            set_kosten_df(edited_k)
            if save_kosten(edited_k):
                st.success("✅ Opgeslagen naar Excel")
                st.rerun()
            else:
                st.error("❌ Excel save mislukt.")

# ── Tab 7: Analyse ─────────────────────────────────────────────────────────
with tabs[6]:
    sec_div("Detailanalyse", "📈")
    df_v = verbouwing().copy()
    if not df_v.empty:
        df_v["Totaal (€)"] = pd.to_numeric(df_v["Totaal (€)"], errors="coerce").fillna(0)
        df_v = df_v[df_v["Totaal (€)"] > 0]

        col_a, col_b = st.columns(2)
        with col_a:
            st.markdown("**🍩 Verdeling per categorie**")
            fig_d = go.Figure(go.Pie(
                labels=list(cats.keys()), values=list(cats.values()),
                hole=0.55, marker_colors=CHART_COLORS, textinfo="label+percent",
                hovertemplate="<b>%{label}</b><br>€ %{value:,.0f}<extra></extra>",
            ))
            fig_d.update_layout(
                plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
                showlegend=False, margin=dict(l=0,r=0,t=0,b=0), height=300,
                annotations=[dict(text=f"<b>€{totaal:,.0f}</b>",
                                  x=0.5,y=0.5,font_size=13,showarrow=False)],
            )
            st.plotly_chart(fig_d, use_container_width=True)
        with col_b:
            st.markdown("**📊 Top 10 duurste posten**")
            top10 = df_v.nlargest(10,"Totaal (€)")[["Post","Categorie","Totaal (€)"]]\
                        .reset_index(drop=True)
            fig_b = px.bar(
                top10, x="Totaal (€)", y="Post", orientation="h",
                color="Categorie", color_discrete_sequence=CHART_COLORS,
                text=top10["Totaal (€)"].apply(lambda x: f"€{x:,.0f}"),
            )
            fig_b.update_traces(textposition="outside")
            fig_b.update_layout(
                plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
                xaxis=dict(tickprefix="€"), showlegend=False,
                margin=dict(l=0,r=80,t=0,b=0), height=300,
            )
            st.plotly_chart(fig_b, use_container_width=True)

        kosten_df = get_kosten_df()
        if not kosten_df.empty and "Fiscaal_Type" in kosten_df.columns:
            st.markdown("**⚖️ Fiscale Samenvatting (HomeZada)**")
            kosten_df["Bedrag (€)"] = pd.to_numeric(kosten_df["Bedrag (€)"], errors="coerce").fillna(0)
            fiscaal_sum = kosten_df.groupby("Fiscaal_Type")["Bedrag (€)"].sum().reset_index()
            fiscaal_sum.columns = ["Fiscaal Type","Totaal (€)"]
            st.dataframe(fiscaal_sum.style.format({"Totaal (€)":"€ {:,.0f}"}),
                         use_container_width=True, hide_index=True)
            if "Verbetering" in fiscaal_sum["Fiscaal Type"].values:
                verb_amt = fiscaal_sum.loc[
                    fiscaal_sum["Fiscaal Type"]=="Verbetering","Totaal (€)"].iloc[0]
                alert(f"💡 € {verb_amt:,.0f} aan Verbeteringen verhoogt de eigenwoningschuld. "
                      "Bewaar alle bonnen voor de belastingaangifte (7 jaar bewaarplicht).", "blu")
    else:
        alert("Geen verbouwingsdata beschikbaar.", "warn")
