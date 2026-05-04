"""
utils/config.py
Centrale configuratie, styling en Excel-mapping voor het Hofakkers 44 Renovatie Dashboard.
"""
from pathlib import Path

APP_CONFIG = {
    "title": "🏠 Hofakkers 44 Renovatie Dashboard",
    "icon": "🏠",
    "layout": "wide",
    "sidebar_state": "expanded",
}

COLORS = {
    "primary": "#FFD700",
    "secondary": "#FF8C00",
    "accent": "#333333",
    "background": "#FFF8DC",
    "surface": "#FFFFFF",
    "muted": "#666666",
    "border": "rgba(0, 0, 0, 0.08)",
}

KAMER_EMOJIS = {
    "Woonkamer": "🛋️",
    "Keuken": "🍳",
    "Badkamer": "🛁",
    "Slaapkamer": "🛏️",
    "Hal": "🚪",
    "Tuin": "🌳",
    "Garage": "🚗",
    "Zolder": "🏠",
    "Kelder": "🏚️",
    "Algemeen": "🏗️",
}

DEFAULT_ROOMS = [
    "Woonkamer", "Keuken", "Badkamer", "Slaapkamer", "Hal",
    "Tuin", "Garage", "Zolder", "Kelder", "Algemeen"
]

TASK_STATUSES = ["Todo", "Bezig", "Gereed"]
WISH_STATUSES = ["Idee", "Gepland", "Gerealiseerd"]
BUDGET_CATEGORIES = ["Materialen", "Arbeid", "Overig"]

DATA_DIR = Path(__file__).parent.parent / "data"
EXCEL_FILE = DATA_DIR / "Begroting_Willianne_Patrick_PRO_v2.xlsx"

CSS_STYLES = """
<style>
body {
    background-color: #FFF8DC;
    color: #333333;
    font-family: 'Inter', sans-serif;
}

section.main {
    padding-top: 0.5rem;
}

.css-1d391kg, .css-1lcbmhc {background: transparent;}

.stApp {
    background: linear-gradient(180deg, #FFF8DC 0%, #FFEFD5 45%, #FFFFFF 100%);
}

.metric-card,
.card,
.tile-card,
.sidebar-card {
    border-radius: 24px;
    box-shadow: 0 18px 40px rgba(0, 0, 0, 0.08);
    border: 1px solid rgba(0, 0, 0, 0.06);
    background: linear-gradient(180deg, rgba(255, 215, 0, 0.95), rgba(255, 140, 0, 0.95));
    color: #111111;
    padding: 22px;
    margin-bottom: 18px;
    transition: transform 0.18s ease, box-shadow 0.18s ease;
}

.metric-card:hover,
.card:hover,
.tile-card:hover,
.sidebar-card:hover {
    transform: translateY(-3px);
    box-shadow: 0 24px 50px rgba(0, 0, 0, 0.15);
}

.tile-card {
    cursor: pointer;
    text-decoration: none;
}

.tile-card h3,
.tile-card h4,
.metric-card h3,
.metric-card h2,
.card h3 {
    color: #111111;
}

.stDataFrame,
.css-1d391kg .stDataFrame {
    border-radius: 20px;
    overflow: hidden;
}

.st-bh {
    border-radius: 18px;
}

.stTextInput>div>div>input,
.stNumberInput>div>div>input,
.stSelectbox>div>div>div>div {
    border-radius: 12px;
}

.block-container {
    padding-top: 1rem;
}

.sidebar .sidebar-content {
    background: #FFD700;
    color: #111111;
}

.css-1lcbmhc {
    background-color: rgba(255, 215, 0, 0.08);
}

.progress-card {
    padding: 18px;
    border-radius: 18px;
    background: #ffffff;
    border: 1px solid rgba(0,0,0,0.08);
    box-shadow: 0 14px 30px rgba(0,0,0,0.06);
}

.progress-bar {
    width: 100%;
    background: rgba(255, 215, 0, 0.25);
    border-radius: 12px;
    height: 18px;
}

.progress-bar-inner {
    height: 100%;
    border-radius: 12px;
    background: linear-gradient(90deg, #FFD700, #FF8C00);
    transition: width 0.4s ease;
}

</style>
"""
