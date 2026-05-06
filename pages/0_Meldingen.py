"""
pages/0_Meldingen.py  –  Hofakkers 44  v4.0
Notificatie hub — alle actieve meldingen op één plek.
"""
import streamlit as st
from utils.ui import page_setup, header, sidebar, sec_div
from utils.state import init, calc_maand_totalen, calc_project
from utils.planning import init_planning
from utils.notifications import render_full_notification_panel, get_notification_counts

page_setup("🔔 Meldingen – Hofakkers 44")
init()
init_planning()

sidebar(calc_maand_totalen(), calc_project())

counts = get_notification_counts()
badge = f" ({counts['totaal']})" if counts["totaal"] > 0 else " (alles OK)"
header(f"🔔 Meldingen{badge}",
       "Proactieve alerts voor budget, cashflow, deadlines en voortgang", "🔔")

render_full_notification_panel()
