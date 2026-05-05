"""
pages/1_Verbouwing.py  –  Hofakkers 44
Verbouwingsbegroting: volledig bewerkbaar, realtime totalen.
"""
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px

from utils.ui import page_setup, inject_css, header, kpi, progress, sidebar
from utils.state import (
    init, calc_maand_totalen, calc_project, calc_verbouwing_totalen,
    verbouwing, set_verbouwing,
)
from utils.config import CHART_COLORS, VERB_CATS, EENHEDEN
from utils.excel_handler import save_verbouwing

page_setup("🔨 Verbouwing – Hofakkers 44")
init()

sidebar(calc_maand_totalen(), calc_project())
header("🔨 Verbouwingsbegroting", "Hofakkers 44 · Volledig bewerkbaar · Realtime totalen")

verb_info = calc_verbouwing_totalen()
totaal    = verb_info["totaal"]
cats      = verb_info["categorieën"]

# ── KPI rij ─────────────────────────────────────────────────────────────────
c1, c2, c3 = st.columns(3)
with c1:
    kpi("💰 Totaal Verbouwing", f"€ {totaal:,.0f}", "alle categorieën")
with c2:
    biggest = max(cats, key=cats.get) if cats else "—"
    kpi("🏆 Grootste Post", biggest, f"€ {cats.get(biggest,0):,.0f}")
with c3:
    n_posten = len(verbouwing())
    kpi("📋 Aantal Posten", str(n_posten), "regels in begroting")

st.markdown("---")

# ── Tabs ────────────────────────────────────────────────────────────────────
tabs = st.tabs(["📊 Overzicht", "✏️ Begroting Bewerken", "📈 Analyse"])

# ── Tab 1: Overzicht ─────────────────────────────────────────────────────────
with tabs[0]:
    col_l, col_r = st.columns(2)

    with col_l:
        st.markdown("##### 🍩 Budget per Categorie")
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
                margin=dict(l=0, r=0, t=0, b=70), height=360,
                annotations=[dict(text=f"<b>€ {totaal:,.0f}</b>",
                                  x=0.5, y=0.5, font_size=13, showarrow=False)],
            )
            st.plotly_chart(fig, use_container_width=True)

    with col_r:
        st.markdown("##### 📊 Budget per Categorie (bar)")
        if cats:
            df_c = pd.DataFrame({
                "Categorie": list(cats.keys()),
                "Budget (€)": list(cats.values()),
            }).sort_values("Budget (€)", ascending=True)
            fig2 = go.Figure(go.Bar(
                x=df_c["Budget (€)"], y=df_c["Categorie"], orientation="h",
                marker_color=CHART_COLORS[1],
                text=df_c["Budget (€)"].apply(lambda x: f"€{x:,.0f}"),
                textposition="outside",
                hovertemplate="<b>%{y}</b><br>€ %{x:,.0f}<extra></extra>",
            ))
            fig2.update_layout(
                plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
                xaxis=dict(tickprefix="€", showgrid=True, gridcolor="#F3F4F6"),
                margin=dict(l=0, r=80, t=0, b=0), height=320,
            )
            st.plotly_chart(fig2, use_container_width=True)

    # Categorie samenvatting tabel
    st.markdown("##### 📋 Samenvatting per Categorie")
    if cats:
        df_sum = pd.DataFrame([
            {"Categorie": k, "Budget (€)": v, "% van totaal": round(v/totaal*100,1) if totaal else 0}
            for k, v in sorted(cats.items(), key=lambda x: -x[1])
        ])
        st.dataframe(
            df_sum.style.format({"Budget (€)": "€ {:,.0f}", "% van totaal": "{:.1f}%"})
                        .background_gradient(subset=["Budget (€)"], cmap="YlOrBr"),
            use_container_width=True, hide_index=True,
        )

# ── Tab 2: Begroting Bewerken ─────────────────────────────────────────────────
with tabs[1]:
    st.markdown("##### ✏️ Verbouwingsbegroting bewerken")
    st.caption("Wijzig hoeveelheden, eenheden of kosten. 'Totaal (€)' wordt automatisch herberekend. Voeg rijen toe met ➕.")

    df_edit = verbouwing().copy()
    if df_edit.empty:
        df_edit = pd.DataFrame(columns=["Categorie","Post","Aantal","Eenheid","Kosten per eenheid (€)","Totaal (€)","Opmerking"])

    edited = st.data_editor(
        df_edit,
        column_config={
            "Categorie":              st.column_config.SelectboxColumn("Categorie", options=VERB_CATS, width="medium"),
            "Post":                   st.column_config.TextColumn("Post", width="large"),
            "Aantal":                 st.column_config.NumberColumn("Aantal", min_value=0, step=0.5, format="%.1f"),
            "Eenheid":                st.column_config.SelectboxColumn("Eenheid", options=EENHEDEN),
            "Kosten per eenheid (€)": st.column_config.NumberColumn("Kosten/eenheid", format="€ %.2f", min_value=0),
            "Totaal (€)":             st.column_config.NumberColumn("Totaal", format="€ %.2f", disabled=True),
            "Opmerking":              st.column_config.TextColumn("Opmerking", width="medium"),
        },
        num_rows="dynamic",
        use_container_width=True,
        height=500,
        key="editor_verbouwing",
    )

    # Herbereken totalen
    edited = edited.copy()
    edited["Aantal"] = pd.to_numeric(edited["Aantal"], errors="coerce").fillna(0)
    edited["Kosten per eenheid (€)"] = pd.to_numeric(edited["Kosten per eenheid (€)"], errors="coerce").fillna(0)
    edited["Totaal (€)"] = edited["Aantal"] * edited["Kosten per eenheid (€)"]

    nieuw_totaal = edited["Totaal (€)"].sum()
    st.metric("Nieuw Totaal (na wijzigingen)", f"€ {nieuw_totaal:,.2f}",
              delta=f"€ {nieuw_totaal - totaal:+,.2f} t.o.v. huidig")

    col_s1, col_s2 = st.columns(2)
    with col_s1:
        if st.button("💾 Opslaan in App", type="primary", use_container_width=True):
            set_verbouwing(edited)
            st.success("✅ Begroting bijgewerkt!")
            st.rerun()
    with col_s2:
        if st.button("💾 Opslaan naar Excel", use_container_width=True):
            set_verbouwing(edited)
            if save_verbouwing(edited):
                st.success("✅ Opgeslagen naar Excel!")
            else:
                st.error("❌ Excel opslaan mislukt.")

# ── Tab 3: Analyse ────────────────────────────────────────────────────────────
with tabs[2]:
    st.markdown("##### 📈 Detailanalyse per Post")
    df_v = verbouwing().copy()
    if not df_v.empty:
        df_v["Totaal (€)"] = pd.to_numeric(df_v["Totaal (€)"], errors="coerce").fillna(0)

        # Top 10 duurste posten
        top10 = df_v.nlargest(10, "Totaal (€)")[["Post","Categorie","Totaal (€)"]].reset_index(drop=True)
        fig3 = px.bar(
            top10, x="Totaal (€)", y="Post", orientation="h",
            color="Categorie", title="Top 10 duurste posten",
            color_discrete_sequence=CHART_COLORS,
            text=top10["Totaal (€)"].apply(lambda x: f"€{x:,.0f}"),
        )
        fig3.update_traces(textposition="outside")
        fig3.update_layout(
            plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
            xaxis=dict(tickprefix="€"), margin=dict(l=0, r=80, t=40, b=0), height=360,
            legend=dict(orientation="h", y=-0.3),
        )
        st.plotly_chart(fig3, use_container_width=True)

        # Voortgangsbalk per categorie t.o.v. totaal
        st.markdown("##### 📊 Aandeel per Categorie")
        for cat, bedrag in sorted(cats.items(), key=lambda x: -x[1]):
            pct = bedrag / totaal * 100 if totaal else 0
            progress(f"{cat}  (€ {bedrag:,.0f})", pct)
    else:
        st.info("Geen verbouwingsdata beschikbaar.")
