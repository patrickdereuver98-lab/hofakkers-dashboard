"""
config/settings.py
Instellingen en configuratie.
"""
import streamlit as st

# Standaard kamers
DEFAULT_KAMERS = [
    "Woonkamer", "Keuken", "Badkamer", "Slaapkamer", "Hal", 
    "Tuin", "Garage", "Zolder", "Kelder", "Algemeen"
]

# Taak statussen
TASK_STATUSES = ["Todo", "Bezig", "Gereed"]

# Wens statussen
WISH_STATUSES = ["Idee", "Gepland", "Gerealiseerd"]

# Budget categorieën
BUDGET_CATEGORIES = ["Materialen", "Arbeid", "Overig"]

def get_setting(key, default=None):
    """Haal instelling op uit session_state."""
    return st.session_state.get(f'setting_{key}', default)

def set_setting(key, value):
    """Sla instelling op in session_state."""
    st.session_state[f'setting_{key}'] = value