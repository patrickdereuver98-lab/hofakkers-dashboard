"""
pages/2_Inboedel.py  –  Hofakkers 44  v6.0
Zelfde quick-edit drill-down patroon als Verbouwing.
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
    calc_inboedel_totalen, calc_ynab_envelopes,
    inboedel, set_inboedel,
)
from utils.config import CHART_COLORS, INBOEDEL_CATS, EENHEDEN
from utils.excel_handler import save_inboedel
from utils.quick_edit import render_category_grid, render_item_editor
from utils.notifications import render_notification_bar

page_setup("🛋️ Inboedel – Hofakkers 44")
init()

sidebar(calc_maand_totalen(), calc_project())
header("🛋️ Inboedelbegroting", "Klik op een kamer om snel te bewerken", "🛋️")
render_notification_bar(max_visible=2, filter_page="Inboedel")

# ── State ─────────────────────────────────────────────────────────────────
if "inbo_selected_cat" not in st.session_state:
    st.session_state["inbo_selected_cat"] = None

inbo_info = calc_inboedel_totalen()
totaal    = inbo_info["totaal"]
cats      = inbo_info["categorieën"]
ynab      = calc_ynab_envelopes()


def _save_inbo(df: pd.DataFrame) -> None:
    set_inboedel(df)
    save_inboedel(df)


# ── KPI strip ─────────────────────────────────────────────────────────────
c1, c2, c3 = st.columns(3)
with c1: kpi("🛋️ Totaal Inboedel", f"€ {totaal:,.0f}", "alle kamers")
with c2:
    biggest = max(cats, key=cats.get) if cats else "—"
    kpi("🏆 Grootste Kamer", biggest, f"€ {cats.get(biggest,0):,.0f}")
with c3: kpi("📦 Artikelen", str(len(inboedel())), "begrotingsregels")

st.markdown("---")

# ══════════════════════════════════════════════════════════════════════════
# DRILL-DOWN VIEW
# ══════════════════════════════════════════════════════════════════════════
selected_cat = st.session_state.get("inbo_selected_cat")

if selected_cat:
    begroot = cats.get(selected_cat, 0)
    s1, s2 = st.columns(2)
    s1.metric("💰 Begroot kamer", f"€ {begroot:,.2f}")
    items_in_cat = [r for r in inboedel().to_dict("records")
                    if r.get("Categorie") == selected_cat] if not inboedel().empty else []
    s2.metric("📦 Artikelen", str(len(items_in_cat)))
    st.markdown("---")

    render_item_editor(
        df=inboedel(),
        cat=selected_cat,
        state_key="inbo_selected_cat",
        eenheden=EENHEDEN,
        on_save=_save_inbo,
        cat_opties=INBOEDEL_CATS,
        show_eenheid=False,  # Inboedel: eenvoudiger (geen m²/uur nodig)
    )

# ══════════════════════════════════════════════════════════════════════════
# OVERZICHT VIEW
# ══════════════════════════════════════════════════════════════════════════
else:
    tabs = st.tabs([
        "🏘️ Kamers",
        "📬 YNAB Envelopes",
        "🔄 Verschuif Geld",
        "📝 Bulk Editor",
        "📈 Analyse",
    ])

    with tabs[0]:
        sec_div("Klik op een kamer om direct te bewerken", "🏘️")
        render_category_grid(df=inboedel(), cats=cats,
                              state_key="inbo_selected_cat", cols=3)

    with tabs[1]:
        sec_div("YNAB Envelopes", "📬")
        inbo_envs = [e for e in ynab["envelopes"] if e["type"]=="inboedel"]
        if inbo_envs:
            tb = sum(e["begroot"] for e in inbo_envs)
            tr = sum(e["gerealiseerd"] for e in inbo_envs)
            e1,e2,e3 = st.columns(3)
            e1.metric("Begroot",      f"€ {tb:,.0f}")
            e2.metric("Gerealiseerd", f"€ {tr:,.0f}")
            e3.metric("Beschikbaar",  f"€ {tb-tr:,.0f}",
                      delta_color="normal" if tb>=tr else "inverse")
            st.markdown("")
            for e in inbo_envs: render_ynab_row(e)
        else:
            alert("Geen inboedel envelopes.", "warn")

    with tabs[2]:
        sec_div("Verschuif geld", "🔄")
        ynab_transfer_form(envelopes=ynab["envelopes"], vrije_buffer=ynab["vrij"],
                           key_prefix="inbo_ynab")

    with tabs[3]:
        sec_div("Bulk Editor", "📝")
        st.caption("Alle artikelen tegelijk bewerken. Voor snelle per-kamer edits: gebruik 🏘️ Kamers.")
        df_bulk = inboedel().copy()
        if df_bulk.empty:
            df_bulk = pd.DataFrame(columns=["Categorie","Post","Aantal","Eenheid",
                                            "Kosten per eenheid (€)","Totaal (€)","Opmerking"])
        edited = st.data_editor(df_bulk,
            column_config={
                "Categorie":st.column_config.SelectboxColumn("Kamer",options=INBOEDEL_CATS,width="medium"),
                "Post":st.column_config.TextColumn("Artikel",width="large"),
                "Aantal":st.column_config.NumberColumn("Aantal",min_value=0,step=1,format="%.0f"),
                "Eenheid":st.column_config.SelectboxColumn("Eenheid",options=EENHEDEN),
                "Kosten per eenheid (€)":st.column_config.NumberColumn("Kosten/stuk",format="€ %.2f",min_value=0),
                "Totaal (€)":st.column_config.NumberColumn("Totaal",format="€ %.2f",disabled=True),
                "Opmerking":st.column_config.TextColumn("Opmerking"),
            },
            num_rows="dynamic", use_container_width=True, height=500, key="inbo_bulk")
        edited["Aantal"] = pd.to_numeric(edited["Aantal"],errors="coerce").fillna(0)
        edited["Kosten per eenheid (€)"] = pd.to_numeric(edited["Kosten per eenheid (€)"],errors="coerce").fillna(0)
        edited["Totaal (€)"] = edited["Aantal"] * edited["Kosten per eenheid (€)"]
        nieuw = float(edited["Totaal (€)"].sum())
        st.metric("Nieuw Totaal", f"€ {nieuw:,.2f}", delta=f"€ {nieuw-totaal:+,.2f}")
        if st.button("💾 Bulk opslaan", type="primary", use_container_width=True, key="bulk_i_save"):
            _save_inbo(edited); st.success("✅ Opgeslagen!"); st.rerun()

    with tabs[4]:
        sec_div("Detailanalyse", "📈")
        df_v = inboedel().copy()
        if not df_v.empty:
            df_v["Totaal (€)"] = pd.to_numeric(df_v["Totaal (€)"],errors="coerce").fillna(0)
            df_v = df_v[df_v["Totaal (€)"]>0]
            if not df_v.empty:
                col_a,col_b = st.columns(2)
                with col_a:
                    fig_d = go.Figure(go.Pie(labels=list(cats.keys()),values=list(cats.values()),
                        hole=0.55,marker_colors=CHART_COLORS,textinfo="label+percent"))
                    fig_d.update_layout(plot_bgcolor="rgba(0,0,0,0)",paper_bgcolor="rgba(0,0,0,0)",
                        showlegend=True,legend=dict(orientation="h",y=-0.3),
                        margin=dict(l=0,r=0,t=0,b=70),height=300,
                        annotations=[dict(text=f"<b>€{totaal:,.0f}</b>",x=0.5,y=0.5,font_size=13,showarrow=False)])
                    st.plotly_chart(fig_d, use_container_width=True)
                with col_b:
                    top = df_v.nlargest(10,"Totaal (€)")[["Post","Categorie","Totaal (€)"]].reset_index(drop=True)
                    fig_b = px.bar(top,x="Totaal (€)",y="Post",orientation="h",
                                   color="Categorie",color_discrete_sequence=CHART_COLORS,
                                   text=top["Totaal (€)"].apply(lambda x:f"€{x:,.0f}"))
                    fig_b.update_traces(textposition="outside")
                    fig_b.update_layout(plot_bgcolor="rgba(0,0,0,0)",paper_bgcolor="rgba(0,0,0,0)",
                        xaxis=dict(tickprefix="€"),showlegend=False,margin=dict(l=0,r=80,t=0,b=0),height=300)
                    st.plotly_chart(fig_b, use_container_width=True)
                for cat,bedrag in sorted(cats.items(),key=lambda x:-x[1]):
                    progress(f"{cat}  (€{bedrag:,.0f})", bedrag/totaal*100 if totaal else 0)
        else:
            alert("Geen inboedeldata.", "warn")
