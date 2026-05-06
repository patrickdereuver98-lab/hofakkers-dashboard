"""
pages/4_Vermogen.py  –  Hofakkers 44  v3.0
"""
import streamlit as st
import pandas as pd
import plotly.graph_objects as go

from utils.ui import page_setup, header, kpi, progress, sidebar, alert, sec_div
from utils.notifications import render_notification_bar
from utils.state import (
    init, calc_maand_totalen, calc_project,
    calc_spaargeld, dash, set_dashboard,
    sparen, hypotheek,
)
from utils.config import CHART_COLORS
from utils.excel_handler import save_dashboard

page_setup("💎 Vermogen – Hofakkers 44")
init()
sidebar(calc_maand_totalen(), calc_project())
header("💎 Vermogen & Financieel Plan", "Patrick & Willianne · Hofakkers 44", "💎")

render_notification_bar(max_visible=2, filter_page="Dashboard")

proj = calc_project()
verm = calc_spaargeld()
d    = dash()


def sf(v):
    try:
        return float(str(v or 0).replace(",",".").replace("€","").strip())
    except (TypeError, ValueError):
        return 0.0


tabs = st.tabs([
    "📊 Vermogensoverzicht",
    "💹 Sparen & Beleggen",
    "🏦 Hypotheek",
    "✏️ Waarden Aanpassen",
])

# ══════════════════════════════════════════════════════════════════════════════
# TAB 1 – VERMOGENSOVERZICHT
# ══════════════════════════════════════════════════════════════════════════════
with tabs[0]:
    c1, c2, c3, c4 = st.columns(4)
    with c1: kpi("👤 Patrick",      f"€ {verm['patrick']:,.0f}",       "resterend", "blu")
    with c2: kpi("👤 Willianne",    f"€ {verm['willianne']:,.0f}",     "resterend", "grn")
    with c3: kpi("💎 Samen",        f"€ {verm['samen']:,.0f}",         "gezamenlijk")
    with c4: kpi("🏦 Nu Gespaard",  f"€ {verm['totaal_sparen']:,.0f}", "sparen+beleggen")

    st.markdown("---")
    col_l, col_r = st.columns(2)

    with col_l:
        sec_div("Vermogensverdeling na Verbouwing", "🍩")
        pat_v, wil_v = max(verm["patrick"],0), max(verm["willianne"],0)
        if pat_v + wil_v > 0:
            fig = go.Figure(go.Pie(
                labels=["Patrick","Willianne"], values=[pat_v, wil_v],
                hole=0.55, marker_colors=["#3B82F6","#10B981"],
                textinfo="label+value+percent",
                hovertemplate="<b>%{label}</b><br>€ %{value:,.0f}<extra></extra>",
            ))
            fig.update_layout(
                plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
                showlegend=False, margin=dict(l=0,r=0,t=0,b=0), height=300,
                annotations=[dict(text=f"<b>€{verm['samen']:,.0f}</b><br>samen",
                                  x=0.5,y=0.5,font_size=12,showarrow=False)],
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            alert("Vul vermogenswaarden in via 'Waarden Aanpassen'.", "warn")

    with col_r:
        sec_div("Project Berekening (Waterfall)", "📊")
        totaal_nu = verm["totaal_sparen"]
        proj_kost = proj["project"]
        benodigd  = sf(d.get("Benodigd geld woning (aankoopkosten + project)",0))
        aankoop   = max(benodigd - proj_kost, 0)
        resterend = verm["samen"]

        if totaal_nu > 0:
            fig2 = go.Figure(go.Waterfall(
                orientation="v",
                measure=["absolute","relative","relative","total"],
                x=["💰 Huidig Vermogen","🔨 Project","🏠 Aankoopkosten","💎 Resterend"],
                y=[totaal_nu, -proj_kost, -aankoop, 0],
                connector=dict(line=dict(color="#E5E7EB")),
                increasing=dict(marker_color="#10B981"),
                decreasing=dict(marker_color="#EF4444"),
                totals=dict(marker_color="#3B82F6"),
                text=[f"€{totaal_nu:,.0f}",f"-€{proj_kost:,.0f}",
                      f"-€{aankoop:,.0f}",f"€{resterend:,.0f}"],
                textposition="outside",
            ))
            fig2.update_layout(
                plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
                margin=dict(l=0,r=0,t=10,b=0), height=300, showlegend=False,
                yaxis=dict(tickprefix="€"),
            )
            st.plotly_chart(fig2, use_container_width=True)
        else:
            alert("Vul 'Totaal sparen + beleggen nu' in via Waarden Aanpassen.", "warn")

    st.markdown("---")
    sec_div("Volledig Projectoverzicht", "📋")
    proj_tabel = [
        ("💰 Huidig gezamenlijk vermogen",    verm["totaal_sparen"]),
        ("🔨 Verbouwingskosten",               proj["verbouwing"]),
        ("🛋️ Inboedelkosten",                 proj["inboedel"]),
        ("📦 Totaal projectkosten",            proj["project"]),
        ("🏠 Aankoopkosten woning",            aankoop),
        ("👤 Benodigd per persoon",            proj["per_persoon"]),
        ("💎 Gezamenlijk resterend vermogen",  verm["samen"]),
        ("👤 Patrick resterend",               verm["patrick"]),
        ("👤 Willianne resterend",             verm["willianne"]),
    ]
    df_p = pd.DataFrame(proj_tabel, columns=["Omschrijving","Bedrag (€)"])
    st.dataframe(
        df_p.style.format({"Bedrag (€)":"€ {:,.0f}"})
                  .applymap(lambda x: "color:#10B981;font-weight:600" if isinstance(x,(int,float)) and x>0
                            else ("color:#EF4444;font-weight:600" if isinstance(x,(int,float)) and x<0 else ""),
                            subset=["Bedrag (€)"]),
        use_container_width=True, hide_index=True,
    )

# ══════════════════════════════════════════════════════════════════════════════
# TAB 2 – SPAREN & BELEGGEN
# ══════════════════════════════════════════════════════════════════════════════
with tabs[1]:
    sp = sparen()
    sec_div("Spaarprojektie", "💹")
    s1, s2, s3, s4 = st.columns(4)
    s1.metric("Startwaarde", f"€ {sp.get('startwaarde',0):,.0f}")
    s2.metric("Maandinleg",  f"€ {sp.get('maandinleg', 0):,.0f}")
    s3.metric("Rendement",   f"{sp.get('rendement',0)*100:.1f}% p.j.")
    s4.metric("Periode",     f"{sp.get('periode',0)} jaar")

    tabel = sp.get("tabel", pd.DataFrame())
    if not tabel.empty:
        sec_div("Vermogensopbouw Projectie", "📈")
        fig_sp = go.Figure()
        fig_sp.add_trace(go.Scatter(
            x=tabel["Jaar"], y=tabel["Eindwaarde (€)"],
            mode="lines+markers", name="Eindwaarde",
            line=dict(color="#FFD700",width=3),
            fill="tozeroy", fillcolor="rgba(255,215,0,0.12)",
            hovertemplate="Jaar %{x}: € %{y:,.0f}<extra></extra>",
        ))
        fig_sp.update_layout(
            plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
            xaxis=dict(title="Jaar",showgrid=True,gridcolor="#F3F4F6"),
            yaxis=dict(title="Vermogen",tickprefix="€"),
            height=320, margin=dict(l=0,r=0,t=10,b=0),
        )
        st.plotly_chart(fig_sp, use_container_width=True)

        with st.expander("📋 Volledige projectietabel"):
            st.dataframe(tabel.style.format({c:"€ {:,.0f}" for c in tabel.columns if "€" in c}),
                         use_container_width=True, hide_index=True)
    else:
        alert("Geen spaarprojectie gevonden in tabblad 'Sparen & Beleggen'.", "warn")

# ══════════════════════════════════════════════════════════════════════════════
# TAB 3 – HYPOTHEEK
# ══════════════════════════════════════════════════════════════════════════════
with tabs[2]:
    hyp     = hypotheek()
    params  = hyp.get("params",{})
    tabel_h = hyp.get("tabel", pd.DataFrame())

    sec_div("Hypotheekparameters", "🏦")
    if params:
        cols_h = st.columns(3)
        for i, (k,v) in enumerate(params.items()):
            with cols_h[i%3]:
                try:
                    fv = float(v)
                    label = (f"€ {fv:,.0f}" if any(w in k.lower() for w in ("bedrag","schuld","kosten"))
                             else f"{fv*100:.2f}%" if "rente" in k.lower() else str(v))
                except (TypeError, ValueError):
                    label = str(v)
                st.metric(k, label)
    else:
        alert("Geen hypotheekparameters in tabblad 'Hypotheek'.", "warn")

    if not tabel_h.empty and "Maand" in tabel_h.columns:
        sec_div("Aflossingsverloop", "📉")
        fig_h = go.Figure()
        for col, color, name in [("Restschuld (€)","#EF4444","Restschuld"),
                                  ("Rente (€)",     "#F59E0B","Rente"),
                                  ("Aflossing (€)", "#10B981","Aflossing")]:
            if col in tabel_h.columns:
                fig_h.add_trace(go.Scatter(
                    x=tabel_h["Maand"], y=tabel_h[col],
                    mode="lines", name=name, line=dict(color=color,width=2),
                    hovertemplate=f"Maand %{{x}}: € %{{y:,.0f}}<extra>{name}</extra>",
                ))
        fig_h.update_layout(
            plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
            xaxis=dict(title="Maand"), yaxis=dict(title="Bedrag (€)",tickprefix="€"),
            legend=dict(orientation="h",y=-0.2),
            height=320, margin=dict(l=0,r=0,t=10,b=50),
        )
        st.plotly_chart(fig_h, use_container_width=True)

        with st.expander("📋 Volledige annuïteitentabel"):
            st.dataframe(tabel_h.style.format({c:"€ {:,.2f}" for c in tabel_h.columns if "€" in c}),
                         use_container_width=True, hide_index=True, height=400)

# ══════════════════════════════════════════════════════════════════════════════
# TAB 4 – WAARDEN AANPASSEN (gegroepeerd)
# ══════════════════════════════════════════════════════════════════════════════
with tabs[3]:
    sec_div("Vermogenswaarden Aanpassen", "✏️")
    st.caption("Directe koppeling met 'Dashboard PRO'. Klik 'Opslaan' om Excel + backup bij te werken.")

    # Gegroepeerde sleutels voor betere UX
    groepen = {
        "👥 Persoonlijk Vermogen": [
            "Totaal sparen + beleggen nu",
            "Vermogen Patrick na verbouwing",
            "Vermogen Willianne na verbouwing",
            "Samen vermogen na verbouwing",
        ],
        "🏗️ Project Kosten": [
            "Verbouwing (totaal)",
            "Inboedel (totaal)",
            "Projectkosten samen (verbouwing + inboedel)",
        ],
        "🏠 Woning Aankoop": [
            "Benodigd geld woning (aankoopkosten + project)",
            "Benodigd per persoon",
        ],
    }

    updated = dict(d)
    for groep_naam, keys in groepen.items():
        st.markdown(f"##### {groep_naam}")
        cols_g = st.columns(2)
        for i, key in enumerate(keys):
            cur = sf(d.get(key, 0)) if key in d else 0.0
            with cols_g[i % 2]:
                new_v = st.number_input(
                    key, value=cur, step=500.0, format="%.2f",
                    key=f"verm_{key}",
                    help="Nog niet ingevuld in Excel" if key not in d else None,
                )
                if new_v != 0.0 or key in d:
                    updated[key] = new_v
        st.markdown("")

    if st.button("💾 Opslaan naar Excel", type="primary", key="verm_save",
                 use_container_width=True):
        set_dashboard(updated)
        if save_dashboard(updated):
            st.success("✅ Opgeslagen naar Excel (backup gemaakt)")
            st.rerun()
        else:
            st.error("❌ Mislukt — is Excel geopend?")
