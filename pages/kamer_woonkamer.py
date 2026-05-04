"""
pages/kamer_woonkamer.py
Kamer pagina voor Woonkamer.
"""
import streamlit as st
import pandas as pd
from ui.layout import inject_css
from ui.sidebar import render_sidebar
from ui.components import render_card, render_metric, render_progress_bar, render_task_card
from utils.state_manager import get_kamer_data, save_kamer_data, get_taken, save_taken, get_wensen, save_wensen, get_kosten, save_kosten
from utils.calculations import calculate_budget_per_kamer
from config.settings import TASK_STATUSES, WISH_STATUSES, BUDGET_CATEGORIES
from config.config import KAMER_EMOJIS

# Setup
inject_css()
render_sidebar()

kamer = "Woonkamer"
emoji = KAMER_EMOJIS.get(kamer, "🏠")

# Haal verbouwing data
verbouwing_df = st.session_state.get('verbouwing', pd.DataFrame())

if verbouwing_df.empty:
    st.error("Geen verbouwing data beschikbaar.")
    st.stop()

# Zorg voor Kamer kolom
if 'Kamer' not in verbouwing_df.columns:
    verbouwing_df['Kamer'] = 'Algemeen'

st.title(f"{emoji} {kamer}")

# Tabs
tabs = st.tabs(["Overzicht", "Budget", "Kosten", "Taken", "Wensen", "Configuratie"])

# Overzicht tab
with tabs[0]:
    st.header("📊 Overzicht")
    
    # Budget status
    budget_data = calculate_budget_per_kamer()
    kamer_budget = next((k for k in budget_data if k['kamer'] == kamer), {'budget': 0, 'besteed': 0, 'resterend': 0})
    
    col1, col2, col3 = st.columns(3)
    with col1:
        render_metric("💰 Budget", f"€ {kamer_budget['budget']:,.0f}")
    with col2:
        render_metric("✅ Besteed", f"€ {kamer_budget['besteed']:,.0f}")
    with col3:
        render_metric("🎯 Resterend", f"€ {kamer_budget['resterend']:,.0f}")
    
    # Voortgang
    totaal_taken = len(get_taken(kamer))
    gereed_taken = len([t for t in get_taken(kamer) if t.get('status') == 'Gereed'])
    voortgang = (gereed_taken / totaal_taken * 100) if totaal_taken > 0 else 0
    
    render_progress_bar(voortgang, 100, "Voortgang Taken")
    
    # Taken samenvatting
    render_card("Taken Status", f"Totaal: {totaal_taken}, Gereed: {gereed_taken}")

# Budget tab
with tabs[1]:
    st.header("💰 Budget")
    
    budget_df = get_kamer_data(kamer)
    if not budget_df.empty:
        edited_df = st.data_editor(
            budget_df[['Categorie', 'Post', 'Aantal', 'Eenheid', 'Kosten per eenheid (€)', 'Totaal (€)']],
            column_config={
                "Aantal": st.column_config.NumberColumn("Aantal", min_value=0, step=1),
                "Kosten per eenheid (€)": st.column_config.NumberColumn("Kosten per eenheid (€)", min_value=0.0, step=0.01, format="€ %.2f"),
                "Totaal (€)": st.column_config.NumberColumn("Totaal (€)", min_value=0.0, step=0.01, format="€ %.2f", disabled=True),
            },
            num_rows="dynamic",
            use_container_width=True
        )
        
        # Update totalen
        for idx in edited_df.index:
            aantal = edited_df.at[idx, 'Aantal'] or 0
            kosten = edited_df.at[idx, 'Kosten per eenheid (€)'] or 0
            edited_df.at[idx, 'Totaal (€)'] = aantal * kosten
        
        if st.button("💾 Opslaan Budget", type="primary"):
            save_kamer_data(kamer, edited_df)
            st.success("✅ Budget opgeslagen!")
            st.rerun()
    else:
        st.info("Geen budget data beschikbaar voor deze kamer.")

# Kosten tab
with tabs[2]:
    st.header("🧾 Kosten")
    
    kosten = get_kosten(kamer)
    
    # Nieuwe kosten toevoegen
    with st.form("nieuwe_kosten"):
        st.subheader("Nieuwe Kosten Toevoegen")
        datum = st.date_input("Datum")
        leverancier = st.text_input("Leverancier")
        bedrag = st.number_input("Bedrag (€)", min_value=0.0, step=0.01)
        categorie = st.selectbox("Categorie", BUDGET_CATEGORIES)
        omschrijving = st.text_input("Omschrijving")
        
        if st.form_submit_button("➕ Toevoegen"):
            nieuwe_kost = {
                "Datum": datum.strftime("%Y-%m-%d"),
                "Leverancier": leverancier,
                "Bedrag": bedrag,
                "Categorie": categorie,
                "Omschrijving": omschrijving
            }
            kosten.append(nieuwe_kost)
            save_kosten(kamer, kosten)
            st.success("✅ Kosten toegevoegd!")
            st.rerun()
    
    # Lijst van kosten
    if kosten:
        df = pd.DataFrame(kosten)
        st.dataframe(df, use_container_width=True)
    else:
        st.info("Geen kosten geregistreerd.")

# Taken tab
with tabs[3]:
    st.header("✅ Taken")
    
    taken = get_taken(kamer)
    
    # Nieuwe taak toevoegen
    nieuwe_taak = st.text_input("Nieuwe taak", key=f"taak_{kamer}")
    if st.button("➕ Toevoegen", key=f"add_{kamer}"):
        if nieuwe_taak:
            taken.append({"taak": nieuwe_taak, "status": "Todo"})
            save_taken(kamer, taken)
            st.rerun()
    
    # Taken weergeven in kolommen
    col1, col2, col3 = st.columns(3)
    status_cols = {"Todo": col1, "Bezig": col2, "Gereed": col3}
    
    for status in TASK_STATUSES:
        with status_cols[status]:
            st.subheader(f"{status}")
            status_taken = [t for t in taken if t.get('status') == status]
            for taak in status_taken:
                render_task_card(taak['taak'], status)
                
                # Status veranderen
                cols = st.columns(3)
                for i, new_status in enumerate(TASK_STATUSES):
                    if cols[i].button(f"→ {new_status}", key=f"{kamer}_{taak['taak']}_{new_status}"):
                        taak['status'] = new_status
                        save_taken(kamer, taken)
                        st.rerun()

# Wensen tab
with tabs[4]:
    st.header("💡 Wensen")
    
    wensen = get_wensen(kamer)
    
    # Nieuwe wens toevoegen
    nieuwe_wens = st.text_input("Nieuwe wens", key=f"wens_{kamer}")
    if st.button("➕ Toevoegen", key=f"add_wens_{kamer}"):
        if nieuwe_wens:
            wensen.append({"wens": nieuwe_wens, "status": "Idee"})
            save_wensen(kamer, wensen)
            st.rerun()
    
    # Wensen weergeven
    for wens in wensen:
        status = wens.get('status', 'Idee')
        st.write(f"**{wens['wens']}** - {status}")
        
        # Status veranderen
        cols = st.columns(len(WISH_STATUSES))
        for i, new_status in enumerate(WISH_STATUSES):
            if cols[i].button(f"→ {new_status}", key=f"{kamer}_wens_{wens['wens']}_{new_status}"):
                wens['status'] = new_status
                save_wensen(kamer, wensen)
                st.rerun()

# Configuratie tab
with tabs[5]:
    st.header("⚙️ Configuratie")
    
    st.subheader("Kamer Instellingen")
    st.info("Configuratie opties voor deze kamer kunnen hier worden toegevoegd.")
