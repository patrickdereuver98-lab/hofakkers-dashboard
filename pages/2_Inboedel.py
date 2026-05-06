"""
pages/2_Inboedel.py  –  Hofakkers 44  v3.0
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
    calc_inboedel_totalen, calc_ynab_envelopes,
    inboedel, set_inboedel,
)
from utils.config import CHART_COLORS, INBOEDEL_CATS, EENHEDEN
from utils.excel_handler import save_inboedel

page_setup("🛋️ Inboedel – Hofakkers 44")
init()

sidebar(calc_maand_totalen(), calc_project())
header("🛋️ Inboedelbegroting", "Notion Gallery · Per Kamer · Volledig bewerkbaar", "🛋️")

# Proactieve notificaties (budget-overschrijdingen, deadlines)
render_notification_bar(max_visible=2, filter_page="Inboedel")

inbo_info = calc_inboedel_totalen()
totaal    = inbo_info["totaal"]
cats      = inbo_info["categorieën"]
ynab      = calc_ynab_envelopes()

c1, c2, c3 = st.columns(3)
with c1: kpi("🛋️ Totaal Inboedel", f"€ {totaal:,.0f}", "alle kamers")
with c2:
    biggest = max(cats, key=cats.get) if cats else "—"
    kpi("🏆 Grootste Kamer", biggest, f"€ {cats.get(biggest,0):,.0f}")
with c3: kpi("📦 Aantal Artikelen", str(len(inboedel())), "begrotingsregels")

st.markdown("---")

tabs = st.tabs([
    "🏘️ Kamer Gallery",
    "📬 YNAB Envelopes",
    "🔄 Verschuif Geld",
    "✏️ Begroting Bewerken",
    "📈 Analyse",
])

# ── Tab 1: Notion Gallery ──────────────────────────────────────────────────
with tabs[0]:
    sec_div("Inboedel per Kamer", "🏘️")
    if cats:
        cats_sorted = sorted(cats.items(), key=lambda x: -x[1])
        inbo_envs   = {e["naam"]: e for e in ynab["envelopes"] if e["type"] == "inboedel"}
        df_i        = inboedel()
        cols        = st.columns(3)

        for i, (cat, begroot) in enumerate(cats_sorted):
            env  = inbo_envs.get(cat, {})
            real = env.get("gerealiseerd", 0.0)
            override = env.get("override", 0)
            n    = int(df_i[df_i["Categorie"] == cat].shape[0]) if not df_i.empty else 0
            extra = ""
            if override != 0:
                sign = "+" if override > 0 else ""
                extra = f"⚙️ override {sign}€{override:,.0f}"
            with cols[i % 3]:
                render_room_card(naam=cat, begroot=begroot,
                                 gerealiseerd=real, n_posten=n, extra_caption=extra)

        st.markdown("---")
        col_d, col_b = st.columns(2)
        with col_d:
            st.markdown("**🍩 Verdeling per Kamer**")
            fig = go.Figure(go.Pie(
                labels=list(cats.keys()), values=list(cats.values()),
                hole=0.55, marker_colors=CHART_COLORS, textinfo="label+percent",
                hovertemplate="<b>%{label}</b><br>€ %{value:,.0f}<extra></extra>",
            ))
            fig.update_layout(
                plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
                showlegend=True, legend=dict(orientation="h", y=-0.3),
                margin=dict(l=0,r=0,t=0,b=70), height=320,
                annotations=[dict(text=f"<b>€{totaal:,.0f}</b>",
                                  x=0.5,y=0.5,font_size=13,showarrow=False)],
            )
            st.plotly_chart(fig, use_container_width=True)
        with col_b:
            st.markdown("**📊 Budget per Kamer**")
            df_c = pd.DataFrame({"Kamer":list(cats.keys()),
                                 "Budget (€)":list(cats.values())}
                                ).sort_values("Budget (€)", ascending=True)
            fig2 = go.Figure(go.Bar(
                x=df_c["Budget (€)"], y=df_c["Kamer"], orientation="h",
                marker_color=CHART_COLORS[3],
                text=df_c["Budget (€)"].apply(lambda x: f"€{x:,.0f}"),
                textposition="outside",
            ))
            fig2.update_layout(
                plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
                xaxis=dict(tickprefix="€",showgrid=True,gridcolor="#F3F4F6"),
                margin=dict(l=0,r=100,t=0,b=0), height=max(260,len(cats)*44),
            )
            st.plotly_chart(fig2, use_container_width=True)
    else:
        alert("Geen inboedeldata beschikbaar.", "warn")

# ── Tab 2: YNAB Envelopes ──────────────────────────────────────────────────
with tabs[1]:
    sec_div("YNAB Envelopes", "📬")
    inbo_envs_list = [e for e in ynab["envelopes"] if e["type"] == "inboedel"]
    if inbo_envs_list:
        totaal_b = sum(e["begroot"] for e in inbo_envs_list)
        totaal_r = sum(e["gerealiseerd"] for e in inbo_envs_list)
        avail    = totaal_b - totaal_r
        ec1, ec2, ec3 = st.columns(3)
        ec1.metric("Totaal Begroot",      f"€ {totaal_b:,.0f}")
        ec2.metric("Totaal Gerealiseerd", f"€ {totaal_r:,.0f}")
        ec3.metric("Totaal Beschikbaar",  f"€ {avail:,.0f}",
                   delta_color="normal" if avail >= 0 else "inverse")
        st.markdown("")
        for e in inbo_envs_list:
            render_ynab_row(e)
    else:
        alert("Geen inboedel envelopes.", "warn")

# ── Tab 3: Transfer ────────────────────────────────────────────────────────
with tabs[2]:
    sec_div("Verschuif geld tussen envelopes", "🔄")
    ynab_transfer_form(envelopes=ynab["envelopes"],
                       vrije_buffer=ynab["vrij"],
                       key_prefix="inbo_ynab")

# ── Tab 4: Begroting Bewerken ──────────────────────────────────────────────
with tabs[3]:
    sec_div("Inboedelbegroting bewerken", "✏️")
    df_edit = inboedel().copy()
    edit_cols = ["Categorie","Post","Aantal","Eenheid","Kosten per eenheid (€)","Totaal (€)","Opmerking"]
    for col in edit_cols:
        if col not in df_edit.columns:
            df_edit[col] = "" if col in ("Categorie","Post","Eenheid","Opmerking") else 0.0
    df_edit = df_edit[edit_cols]

    edited = st.data_editor(
        df_edit,
        column_config={
            "Categorie":              st.column_config.SelectboxColumn("Kamer / Categorie", options=INBOEDEL_CATS, width="medium"),
            "Post":                   st.column_config.TextColumn("Artikel", width="large"),
            "Aantal":                 st.column_config.NumberColumn("Aantal", min_value=0, step=1, format="%.0f"),
            "Eenheid":                st.column_config.SelectboxColumn("Eenheid", options=EENHEDEN),
            "Kosten per eenheid (€)": st.column_config.NumberColumn("Kosten/stuk", format="€ %.2f", min_value=0),
            "Totaal (€)":             st.column_config.NumberColumn("Totaal", format="€ %.2f", disabled=True),
            "Opmerking":              st.column_config.TextColumn("Opmerking"),
        },
        num_rows="dynamic", use_container_width=True, height=500, key="editor_inboedel",
    )
    edited = edited.copy()
    edited["Aantal"] = pd.to_numeric(edited["Aantal"], errors="coerce").fillna(0)
    edited["Kosten per eenheid (€)"] = pd.to_numeric(edited["Kosten per eenheid (€)"], errors="coerce").fillna(0)
    edited["Totaal (€)"] = edited["Aantal"] * edited["Kosten per eenheid (€)"]
    nieuw = float(edited["Totaal (€)"].sum())
    st.metric("Nieuw Totaal", f"€ {nieuw:,.2f}", delta=f"€ {nieuw-totaal:+,.2f}")

    if st.button("💾 Opslaan naar Excel", type="primary",
                 use_container_width=True, key="inbo_save"):
        set_inboedel(edited)
        if save_inboedel(edited):
            st.success("✅ Opgeslagen naar Excel (backup gemaakt)")
            st.rerun()
        else:
            st.error("❌ Mislukt — is Excel geopend?")

# ── Tab 5: Analyse ─────────────────────────────────────────────────────────
with tabs[4]:
    sec_div("Detailanalyse", "📈")
    df_v = inboedel().copy()
    if not df_v.empty:
        df_v["Totaal (€)"] = pd.to_numeric(df_v["Totaal (€)"], errors="coerce").fillna(0)
        df_v = df_v[df_v["Totaal (€)"] > 0]
        if not df_v.empty:
            top = df_v.nlargest(10,"Totaal (€)")[["Post","Categorie","Totaal (€)"]].reset_index(drop=True)
            fig3 = px.bar(top, x="Totaal (€)", y="Post", orientation="h",
                          color="Categorie", title="Top 10 duurste artikelen",
                          color_discrete_sequence=CHART_COLORS,
                          text=top["Totaal (€)"].apply(lambda x: f"€{x:,.0f}"))
            fig3.update_traces(textposition="outside")
            fig3.update_layout(
                plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
                xaxis=dict(tickprefix="€"),
                margin=dict(l=0,r=100,t=30,b=60), height=360,
                legend=dict(orientation="h", y=-0.25),
            )
            st.plotly_chart(fig3, use_container_width=True)

            st.markdown("##### Aandeel per Kamer")
            for cat, bedrag in sorted(cats.items(), key=lambda x: -x[1]):
                progress(f"{cat}  (€ {bedrag:,.0f})", bedrag/totaal*100 if totaal else 0)
    else:
        alert("Geen inboedeldata beschikbaar.", "warn")
