"""
config/config.py
Centrale configuratie voor het Hofakkers 44 Renovatie Dashboard.
"""

# Kleurenpalet (Bob de Bouwer stijl: Geel, Oranje, Zwart)
COLORS = {
    "primary": "#FFD700",  # Goudgeel
    "secondary": "#FF8C00",  # Donkeroranje
    "accent": "#000000",    # Zwart
    "background": "#FFF8DC", # Lichtgeel achtergrond
    "success": "#32CD32",   # Groen voor positief
    "warning": "#FFA500",   # Oranje voor waarschuwing
    "danger": "#FF4500",    # Rood voor gevaar
}

# Emojis per kamer
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

# App instellingen
APP_CONFIG = {
    "title": "🏠 Hofakkers 44 Renovatie Dashboard",
    "icon": "🏠",
    "layout": "wide",
    "sidebar_state": "expanded",
}

# Plotly configuratie
PLOTLY_CONFIG = {
    "displayModeBar": False,
    "responsive": True,
    "showlegend": True,
}

# CSS voor animaties en styling
CSS_STYLES = """
<style>
/* Bob de Bouwer Thema */
body {
    background-color: #FFF8DC;
    font-family: 'Arial', sans-serif;
}

/* Hover effecten voor buttons */
.stButton > button:hover {
    transform: scale(1.05);
    transition: all 0.3s ease;
    box-shadow: 0 4px 8px rgba(0,0,0,0.2);
}

/* Animatie voor metrics */
.metric-card {
    background: linear-gradient(135deg, #FFD700, #FF8C00);
    border-radius: 15px;
    padding: 20px;
    margin: 10px 0;
    color: white;
    text-align: center;
    box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    transition: transform 0.3s ease;
}

.metric-card:hover {
    transform: translateY(-5px);
}

/* Sidebar styling */
.sidebar .sidebar-content {
    background-color: #FFD700;
}

/* Tegel styling voor landingspagina */
.stPageLink {
    background: linear-gradient(135deg, #FFD700, #FF8C00);
    border-radius: 20px;
    padding: 30px;
    margin: 15px 0;
    text-align: center;
    color: white !important;
    box-shadow: 0 6px 12px rgba(0,0,0,0.15);
    transition: all 0.3s ease;
    cursor: pointer;
    display: block;
    text-decoration: none;
}

.stPageLink:hover {
    transform: translateY(-10px) scale(1.02);
    box-shadow: 0 10px 20px rgba(0,0,0,0.25);
    text-decoration: none;
}

/* Progress bar styling */
.progress-bar {
    height: 20px;
    border-radius: 10px;
    background-color: #FFD700;
}

/* Data editor styling */
.stDataFrame {
    border-radius: 10px;
    overflow: hidden;
}
</style>
"""