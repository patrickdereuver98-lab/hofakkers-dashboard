"""
pages/1_Verbouwing.py  –  Hofakkers 44  v6.0

UX volledig herwerkt:
  - Klik op categorie → drill-down view
  - Inline bewerkbare rijen (geen data_editor meer voor snelle edits)
  - Quick-add formulier: naam + bedrag → direct opgeslagen
"""
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px

from utils.ui import (
    page_setup, header, kpi, progress, sidebar,
    alert, sec_div, render_ynab_row, ynab_transfer_form,
)
from utils.state import (
    init, calc_maand_totalen, calc_project,
    calc_verbouwing_totalen, calc_ynab_envelopes, calc_budget_vs_actuals,
    verbouwing, set_verbouwing,
    get_kosten_df, set_kosten_df,
)
from utils.config import CHART_COLORS, VERB_CATS, EENHEDEN, FISCAAL_TYPES
from utils.excel_handler import save_verbouwing, save_kosten
from utils.quick_edit import render_category_grid, render_item_editor
from utils.notifications import render_notification_bar

page_setup("🔨 Verbouwing – Hofakkers 44")
init()

sidebar(calc_maand_totalen(), calc_project())
header("🔨 Verbouwingsbegroting", "Klik op een categorie om snel te bewerken", "🔨")
render_notification_bar(max_visible=2, filter_page="Verbouwing")

# ── State: geselecteerde categorie ────────────────────────────────────────
if "verb_selected_cat" not in st.session_state:
    st.session_state["verb_selected_cat"] = None

# ── Berekeningen ──────────────────────────────────────────────────────────
verb_info = calc_verbouwing_totalen()
totaal    = verb_info["totaal"]
cats      = verb_info["categorieën"]
ynab      = calc_ynab_envelopes()
bva       = calc_budget_vs_actuals()


def _save_verb(df: pd.DataFrame) -> None:
    set_verbouwing(df)
    save_verbouwing(df)


# ── KPI strip ─────────────────────────────────────────────────────────────
real_total = bva[bva["Type"]=="Verbouwing"]["Gerealiseerd (€)"].sum() if not bva.empty else 0
c1, c2, c3, c4 = st.columns(4)
with c1: kpi("💰 Totaal Begroot",   f"€ {totaal:,.0f}")
with c2: kpi("🔨 Gerealiseerd",     f"€ {real_total:,.0f}",
             f"{real_total/totaal*100:.0f}%" if totaal else "")
with c3:
    rest = totaal - real_total
    kpi("🎯 Beschikbaar", f"€ {rest:,.0f}", "", "grn" if rest >= 0 else "red")
with c4: kpi("📋 Posten", str(len(verbouwing())), "begrotingsregels")

st.markdown("---")

# ══════════════════════════════════════════════════════════════════════════
# DRILL-DOWN VIEW
# ══════════════════════════════════════════════════════════════════════════
selected_cat = st.session_state.get("verb_selected_cat")

if selected_cat:
    begroot     = cats.get(selected_cat, 0)
    ynab_env    = next((e for e in ynab["envelopes"] if e["naam"] == selected_cat), {})
    gerealiseerd = ynab_env.get("gerealiseerd", 0)
    beschikbaar  = begroot - gerealiseerd

    s1, s2, s3 = st.columns(3)
    s1.metric("💰 Begroot",      f"€ {begroot:,.2f}")
    s2.metric("🔨 Gerealiseerd", f"€ {gerealiseerd:,.2f}")
    s3.metric("🎯 Beschikbaar",  f"€ {beschikbaar:,.2f}",
              delta_color="normal" if beschikbaar >= 0 else "inverse")
    if begroot > 0:
        progress(f"Budget {selected_cat}", min(gerealiseerd/begroot*100, 100))

    st.markdown("---")

    render_item_editor(
        df=verbouwing(),
        cat=selected_cat,
        state_key="verb_selected_cat",
        eenheden=EENHEDEN,
        on_save=_save_verb,
        cat_opties=VERB_CATS,
        show_eenheid=True,
    )

# ══════════════════════════════════════════════════════════════════════════
# OVERZICHT VIEW
# ══════════════════════════════════════════════════════════════════════════
else:
    tabs = st.tabs([
        "🏘️ Categorieën",
        "📊 Budget vs Actuals",
        "📬 YNAB Envelopes",
        "🔄 Verschuif Geld",
        "🧾 Uitgaven",
        "📝 Bulk Editor",
        "📈 Analyse",
    ])

    with tabs[0]:
        sec_div("Klik op een categorie om direct te bewerken", "🏘️")
        kosten_per_cat = {}
        if not bva.empty:
            for _, row in bva[bva["Type"]=="Verbouwing"].iterrows():
                kosten_per_cat[row["Categorie"]] = float(row.get("Gerealiseerd (€)", 0))
        render_category_grid(df=verbouwing(), cats=cats,
                              state_key="verb_selected_cat",
                              kosten_per_cat=kosten_per_cat, cols=3)

    with tabs[1]:
        sec_div("Budget vs Gerealiseerd", "📊")
        verb_bva = bva[bva["Type"]=="Verbouwing"] if not bva.empty else bva
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
                    .applymap(_kleur, subset=["Verschil (€)"])
                    .background_gradient(subset=["% Gebruikt"], cmap="RdYlGn_r", vmin=0, vmax=110),
                use_container_width=True, hide_index=True,
            )
            fig = go.Figure()
            fig.add_trace(go.Bar(name="Begroot", x=verb_bva["Categorie"],
                                 y=verb_bva["Begroot (€)"], marker_color=CHART_COLORS[0]))
            fig.add_trace(go.Bar(name="Gerealiseerd", x=verb_bva["Categorie"],
                                 y=verb_bva["Gerealiseerd (€)"], marker_color=CHART_COLORS[1]))
            fig.update_layout(barmode="group", plot_bgcolor="rgba(0,0,0,0)",
                              paper_bgcolor="rgba(0,0,0,0)", yaxis=dict(tickprefix="€"),
                              legend=dict(orientation="h",y=-0.25),
                              margin=dict(l=0,r=0,t=10,b=60), height=320)
            st.plotly_chart(fig, use_container_width=True)
            for _, row in verb_bva.iterrows():
                progress(f"{row['Categorie']}  (€{row['Gerealiseerd (€)']:,.0f} / €{row['Begroot (€)']:,.0f})",
                         float(row["% Gebruikt"]))
        else:
            alert("Nog geen uitgaven. Gebruik 'Uitgaven'.", "blu")

    with tabs[2]:
        sec_div("YNAB Envelopes", "📬")
        verb_envs = [e for e in ynab["envelopes"] if e["type"]=="verbouwing"]
        if verb_envs:
            tb = sum(e["begroot"] for e in verb_envs)
            tr = sum(e["gerealiseerd"] for e in verb_envs)
            e1,e2,e3 = st.columns(3)
            e1.metric("Begroot",      f"€ {tb:,.0f}")
            e2.metric("Gerealiseerd", f"€ {tr:,.0f}")
            e3.metric("Beschikbaar",  f"€ {tb-tr:,.0f}",
                      delta_color="normal" if tb>=tr else "inverse")
            st.markdown("")
            for e in verb_envs: render_ynab_row(e)
        else:
            alert("Geen envelopes.", "warn")

    with tabs[3]:
        sec_div("Verschuif geld", "🔄")
        ynab_transfer_form(envelopes=ynab["envelopes"], vrije_buffer=ynab["vrij"],
                           key_prefix="verb_ynab")

    with tabs[4]:
        sec_div("Uitgaven Registreren — Fiscale Audit Trail", "🧾")
        st.caption("Koppel uitgaven aan categorie en fiscaal type (bewaarplicht 7 jaar).")
        kosten_df = get_kosten_df()

        with st.form("kosten_form_verb", clear_on_submit=True):
            f1, f2, f3 = st.columns(3)
            with f1:
                datum       = st.date_input("Datum")
                leverancier = st.text_input("Leverancier")
            with f2:
                bedrag    = st.number_input("Bedrag (€)", min_value=0.0, step=0.01, format="%.2f")
                categorie = st.selectbox("Categorie", VERB_CATS)
            with f3:
                fiscaal   = st.selectbox("Fiscaal Type", FISCAAL_TYPES)
                post_ref  = st.text_input("Post Referentie")
                omschr    = st.text_area("Omschrijving", height=68)

            if st.form_submit_button("➕ Toevoegen", type="primary", use_container_width=True):
                if leverancier.strip() and bedrag > 0:
                    new_row = {"Datum":str(datum),"Leverancier":leverancier.strip(),
                               "Bedrag (€)":bedrag,"Categorie":categorie,
                               "Omschrijving":omschr,"Fiscaal_Type":fiscaal,
                               "Post_Ref":post_ref,"Bon_Ref":""}
                    kosten_df = pd.concat([kosten_df, pd.DataFrame([new_row])], ignore_index=True) \
                                if not kosten_df.empty else pd.DataFrame([new_row])
                    set_kosten_df(kosten_df)
                    save_kosten(kosten_df)
                    st.success(f"✅ € {bedrag:.2f} van {leverancier} opgeslagen!")
                    st.rerun()
                else:
                    st.warning("Vul leverancier en bedrag in.")

        if not kosten_df.empty and "Bedrag (€)" in kosten_df.columns:
            st.metric("Totaal uitgaven", f"€ {kosten_df['Bedrag (€)'].sum():,.2f}")
            edited_k = st.data_editor(kosten_df,
                column_config={"Bedrag (€)":st.column_config.NumberColumn("Bedrag",format="€ %.2f"),
                               "Fiscaal_Type":st.column_config.SelectboxColumn("Fiscaal",options=FISCAAL_TYPES),
                               "Categorie":st.column_config.SelectboxColumn("Categorie",options=VERB_CATS+["Overig"])},
                num_rows="dynamic", use_container_width=True, height=260, key="k_edit_verb")
            if st.button("💾 Opslaan", type="primary", key="save_k_v"):
                set_kosten_df(edited_k); save_kosten(edited_k)
                st.success("✅ Opgeslagen!"); st.rerun()

    with tabs[5]:
        sec_div("Bulk Editor", "📝")
        st.caption("Alle posten tegelijk bewerken. Voor snelle per-categorie edits: gebruik 🏘️ Categorieën.")
        df_bulk = verbouwing().copy()
        if df_bulk.empty:
            df_bulk = pd.DataFrame(columns=["Categorie","Post","Aantal","Eenheid",
                                            "Kosten per eenheid (€)","Totaal (€)","Opmerking"])
        edited = st.data_editor(df_bulk,
            column_config={
                "Categorie":st.column_config.SelectboxColumn("Categorie",options=VERB_CATS,width="medium"),
                "Post":st.column_config.TextColumn("Post",width="large"),
                "Aantal":st.column_config.NumberColumn("Aantal",min_value=0,step=0.5,format="%.1f"),
                "Eenheid":st.column_config.SelectboxColumn("Eenheid",options=EENHEDEN),
                "Kosten per eenheid (€)":st.column_config.NumberColumn("Kosten/eenheid",format="€ %.2f",min_value=0),
                "Totaal (€)":st.column_config.NumberColumn("Totaal",format="€ %.2f",disabled=True),
                "Opmerking":st.column_config.TextColumn("Opmerking"),
            },
            num_rows="dynamic", use_container_width=True, height=480, key="verb_bulk")
        edited["Aantal"] = pd.to_numeric(edited["Aantal"],errors="coerce").fillna(0)
        edited["Kosten per eenheid (€)"] = pd.to_numeric(edited["Kosten per eenheid (€)"],errors="coerce").fillna(0)
        edited["Totaal (€)"] = edited["Aantal"] * edited["Kosten per eenheid (€)"]
        nieuw = float(edited["Totaal (€)"].sum())
        st.metric("Nieuw totaal", f"€ {nieuw:,.2f}", delta=f"€ {nieuw-totaal:+,.2f}")
        if st.button("💾 Bulk opslaan", type="primary", use_container_width=True, key="bulk_v_save"):
            _save_verb(edited); st.success("✅ Opgeslagen!"); st.rerun()

    with tabs[6]:
        sec_div("Detailanalyse", "📈")
        df_v = verbouwing().copy()
        if not df_v.empty:
            df_v["Totaal (€)"] = pd.to_numeric(df_v["Totaal (€)"],errors="coerce").fillna(0)
            df_v = df_v[df_v["Totaal (€)"]>0]
            if not df_v.empty:
                col_a,col_b = st.columns(2)
                with col_a:
                    fig_d = go.Figure(go.Pie(labels=list(cats.keys()),values=list(cats.values()),
                        hole=0.55,marker_colors=CHART_COLORS,textinfo="label+percent"))
                    fig_d.update_layout(plot_bgcolor="rgba(0,0,0,0)",paper_bgcolor="rgba(0,0,0,0)",
                        showlegend=False,margin=dict(l=0,r=0,t=0,b=0),height=280,
                        annotations=[dict(text=f"<b>€{totaal:,.0f}</b>",x=0.5,y=0.5,font_size=13,showarrow=False)])
                    st.plotly_chart(fig_d, use_container_width=True)
                with col_b:
                    top10 = df_v.nlargest(10,"Totaal (€)")[["Post","Categorie","Totaal (€)"]].reset_index(drop=True)
                    fig_b = px.bar(top10,x="Totaal (€)",y="Post",orientation="h",
                                   color="Categorie",color_discrete_sequence=CHART_COLORS,
                                   text=top10["Totaal (€)"].apply(lambda x:f"€{x:,.0f}"))
                    fig_b.update_traces(textposition="outside")
                    fig_b.update_layout(plot_bgcolor="rgba(0,0,0,0)",paper_bgcolor="rgba(0,0,0,0)",
                        xaxis=dict(tickprefix="€"),showlegend=False,margin=dict(l=0,r=80,t=0,b=0),height=280)
                    st.plotly_chart(fig_b, use_container_width=True)
                for cat,bedrag in sorted(cats.items(),key=lambda x:-x[1]):
                    progress(f"{cat}  (€{bedrag:,.0f})", bedrag/totaal*100 if totaal else 0)
        else:
            alert("Geen verbouwingsdata.", "warn")
