"""
pages/2_Inboedel.py  –  Hofakkers 44
Inboedelbegroting per kamer: volledig bewerkbaar.
"""
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px

from utils.ui import page_setup, header, kpi, progress, sidebar
from utils.state import (
    init, calc_maand_totalen, calc_project, calc_inboedel_totalen,
    inboedel, set_inboedel,
)
from utils.config import CHART_COLORS, INBOEDEL_CATS, EENHEDEN
from utils.excel_handler import save_inboedel

page_setup("🛋️ Inboedel – Hofakkers 44")
init()

sidebar(calc_maand_totalen(), calc_project())
header("🛋️ Inboedelbegroting", "Per kamer · Volledig bewerkbaar · Realtime totalen")

inbo_info = calc_inboedel_totalen()
totaal    = inbo_info["totaal"]
cats      = inbo_info["categorieën"]

# ── KPI's ───────────────────────────────────────────────────────────────────
c1, c2, c3 = st.columns(3)
with c1:
    kpi("🛋️ Totaal Inboedel", f"€ {totaal:,.0f}", "alle kamers")
with c2:
    biggest = max(cats, key=cats.get) if cats else "—"
    kpi("🏆 Grootste Post", biggest, f"€ {cats.get(biggest,0):,.0f}")
with c3:
    kpi("📦 Aantal Posten", str(len(inboedel())), "artikelen")

st.markdown("---")

tabs = st.tabs(["📊 Overzicht", "✏️ Begroting Bewerken", "📈 Analyse"])

# ── Tab 1: Overzicht ─────────────────────────────────────────────────────────
with tabs[0]:
    col_l, col_r = st.columns(2)
    with col_l:
        st.markdown("##### 🍩 Budget per Kamer/Categorie")
        if cats:
            fig = go.Figure(go.Pie(
                labels=list(cats.keys()),
                values=list(cats.values()),
                hole=0.55,
                marker_colors=CHART_COLORS,
                textinfo="label+percent",
                hovertemplate="<b>%{label}</b><br>€ %{value:,.0f}<br>%{percent}<extra></extra>",
            ))
            fig.update_layout(
                plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
                showlegend=True, legend=dict(orientation="h", y=-0.3),
                margin=dict(l=0,r=0,t=0,b=70), height=360,
                annotations=[dict(text=f"<b>€ {totaal:,.0f}</b>",
                                  x=0.5, y=0.5, font_size=13, showarrow=False)],
            )
            st.plotly_chart(fig, use_container_width=True)

    with col_r:
        st.markdown("##### 📊 Budget per Kamer")
        if cats:
            df_c = pd.DataFrame({"Kamer": list(cats.keys()), "Bedrag": list(cats.values())}).sort_values("Bedrag", ascending=True)
            fig2 = go.Figure(go.Bar(
                x=df_c["Bedrag"], y=df_c["Kamer"], orientation="h",
                marker_color=CHART_COLORS[3],
                text=df_c["Bedrag"].apply(lambda x: f"€{x:,.0f}"),
                textposition="outside",
            ))
            fig2.update_layout(
                plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
                xaxis=dict(tickprefix="€", showgrid=True, gridcolor="#F3F4F6"),
                margin=dict(l=0,r=80,t=0,b=0), height=320,
            )
            st.plotly_chart(fig2, use_container_width=True)

    st.markdown("##### 📋 Samenvatting per Kamer")
    if cats:
        df_sum = pd.DataFrame([
            {"Kamer": k, "Budget (€)": v, "% van totaal": round(v/totaal*100,1) if totaal else 0}
            for k, v in sorted(cats.items(), key=lambda x: -x[1])
        ])
        st.dataframe(
            df_sum.style.format({"Budget (€)": "€ {:,.0f}", "% van totaal": "{:.1f}%"})
                        .background_gradient(subset=["Budget (€)"], cmap="YlOrBr"),
            use_container_width=True, hide_index=True,
        )

# ── Tab 2: Bewerken ───────────────────────────────────────────────────────────
with tabs[1]:
    st.markdown("##### ✏️ Inboedelbegroting bewerken")
    st.caption("Pas aantallen, eenheden en kosten aan. Totaal wordt automatisch herberekend.")

    df_edit = inboedel().copy()
    if df_edit.empty:
        df_edit = pd.DataFrame(columns=["Categorie","Post","Aantal","Eenheid","Kosten per eenheid (€)","Totaal (€)","Opmerking"])

    edited = st.data_editor(
        df_edit,
        column_config={
            "Categorie":              st.column_config.SelectboxColumn("Kamer/Categorie", options=INBOEDEL_CATS, width="medium"),
            "Post":                   st.column_config.TextColumn("Artikel", width="large"),
            "Aantal":                 st.column_config.NumberColumn("Aantal", min_value=0, step=1, format="%.0f"),
            "Eenheid":                st.column_config.SelectboxColumn("Eenheid", options=EENHEDEN),
            "Kosten per eenheid (€)": st.column_config.NumberColumn("Kosten/stuk", format="€ %.2f", min_value=0),
            "Totaal (€)":             st.column_config.NumberColumn("Totaal", format="€ %.2f", disabled=True),
            "Opmerking":              st.column_config.TextColumn("Opmerking"),
        },
        num_rows="dynamic",
        use_container_width=True,
        height=500,
        key="editor_inboedel",
    )

    edited = edited.copy()
    edited["Aantal"] = pd.to_numeric(edited["Aantal"], errors="coerce").fillna(0)
    edited["Kosten per eenheid (€)"] = pd.to_numeric(edited["Kosten per eenheid (€)"], errors="coerce").fillna(0)
    edited["Totaal (€)"] = edited["Aantal"] * edited["Kosten per eenheid (€)"]
    nieuw = edited["Totaal (€)"].sum()
    st.metric("Nieuw Totaal", f"€ {nieuw:,.2f}", delta=f"€ {nieuw - totaal:+,.2f}")

    col1, col2 = st.columns(2)
    with col1:
        if st.button("💾 Opslaan in App", type="primary", use_container_width=True):
            set_inboedel(edited)
            st.success("✅ Bijgewerkt!")
            st.rerun()
    with col2:
        if st.button("💾 Opslaan naar Excel", use_container_width=True):
            set_inboedel(edited)
            if save_inboedel(edited):
                st.success("✅ Naar Excel!")
            else:
                st.error("❌ Mislukt.")

# ── Tab 3: Analyse ─────────────────────────────────────────────────────────
with tabs[2]:
    df_v = inboedel().copy()
    if not df_v.empty:
        df_v["Totaal (€)"] = pd.to_numeric(df_v["Totaal (€)"], errors="coerce").fillna(0)
        top = df_v.nlargest(10, "Totaal (€)")[["Post","Categorie","Totaal (€)"]].reset_index(drop=True)
        fig3 = px.bar(
            top, x="Totaal (€)", y="Post", orientation="h",
            color="Categorie", title="Top 10 duurste artikelen",
            color_discrete_sequence=CHART_COLORS,
            text=top["Totaal (€)"].apply(lambda x: f"€{x:,.0f}"),
        )
        fig3.update_traces(textposition="outside")
        fig3.update_layout(
            plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
            xaxis=dict(tickprefix="€"), margin=dict(l=0,r=80,t=40,b=60),
            height=360, legend=dict(orientation="h", y=-0.3),
        )
        st.plotly_chart(fig3, use_container_width=True)

        st.markdown("##### Aandeel per Kamer")
        for cat, bedrag in sorted(cats.items(), key=lambda x: -x[1]):
            pct = bedrag / totaal * 100 if totaal else 0
            progress(f"{cat}  (€ {bedrag:,.0f})", pct)
    else:
        st.info("Geen inboedeldata.")
