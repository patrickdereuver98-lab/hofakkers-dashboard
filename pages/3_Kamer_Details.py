import streamlit as st
import pandas as pd
from ui.layout import render_sidebar, inject_css
from utils.calculations import update_verbouwing_totals
from config.config import KAMER_EMOJIS

# Setup
inject_css()
render_sidebar()

st.title("🏠 Kamer Details")

# Helper functie voor emoji
def get_kamer_emoji(kamer):
    return KAMER_EMOJIS.get(kamer, "🔨")

# Haal verbouwing data
verbouwing_df = st.session_state.get('verbouwing', pd.DataFrame())

if verbouwing_df.empty:
    st.error("Geen verbouwing data beschikbaar.")
    st.stop()

# Haal unieke kamers
if 'Kamer' not in verbouwing_df.columns:
    verbouwing_df['Kamer'] = 'Algemeen'

unique_kamers = sorted(verbouwing_df['Kamer'].dropna().unique())

# Grid layout voor kamer selectie
st.subheader("Selecteer een Kamer")
cols = st.columns(4)
actieve_kamer = st.session_state.get('actieve_kamer', unique_kamers[0] if unique_kamers else None)

for idx, kamer in enumerate(unique_kamers):
    col_idx = idx % 4
    emoji = get_kamer_emoji(kamer)
    is_active = (kamer == actieve_kamer)
    if cols[col_idx].button(f"{emoji} {kamer}", key=f"kamer_{kamer}", type="primary" if is_active else "secondary"):
        st.session_state['actieve_kamer'] = kamer
        st.rerun()

# Filter data voor actieve kamer
if actieve_kamer:
    kamer_df = verbouwing_df[verbouwing_df['Kamer'] == actieve_kamer].copy()
    
    st.subheader(f"🔧 Actieplan voor {get_kamer_emoji(actieve_kamer)} {actieve_kamer}")
    
    # Data editor voor deze kamer
    edited_kamer_df = st.data_editor(
        kamer_df,
        column_config={
            "Categorie": st.column_config.TextColumn("Categorie"),
            "Post": st.column_config.TextColumn("Post"),
            "Aantal": st.column_config.NumberColumn("Aantal", min_value=0, step=1),
            "Eenheid": st.column_config.TextColumn("Eenheid"),
            "Kosten per eenheid (€)": st.column_config.NumberColumn("Kosten per eenheid (€)", min_value=0.0, step=0.01, format="€ %.2f"),
            "Totaal (€)": st.column_config.NumberColumn("Totaal (€)", min_value=0.0, step=0.01, format="€ %.2f", disabled=True),
            "Opmerking": st.column_config.TextColumn("Opmerking"),
            "Kamer": st.column_config.TextColumn("Kamer", disabled=True),
        },
        num_rows="dynamic",
        use_container_width=True
    )
    
    # Update totalen
    edited_kamer_df = update_verbouwing_totals(edited_kamer_df)
    
    # Opslaan
    if st.button("💾 Opslaan Wijzigingen", type="primary"):
        # Inject terug in master dataframe
        master_df = verbouwing_df[verbouwing_df['Kamer'] != actieve_kamer]
        master_df = pd.concat([master_df, edited_kamer_df], ignore_index=True)
        st.session_state['verbouwing'] = master_df
        
        # Sla op naar Excel
        from utils.excel_handler import save_verbouwing_data
        if save_verbouwing_data(master_df):
            st.success("✅ Wijzigingen opgeslagen in Excel!")
            st.rerun()
        else:
            st.error("❌ Opslaan mislukt.")
else:
    st.info("Selecteer een kamer om te beginnen.")