"""
utils/config.py
Centrale configuratie voor het Hofakkers 44 Renovatie Dashboard.
Bob de Bouwer SaaS – Stijlvol, Geel, Interactief.
"""
from pathlib import Path

# ── Paden ──────────────────────────────────────────────────────────────────
DATA_DIR   = Path(__file__).parent.parent / "data"
EXCEL_FILE = DATA_DIR / "Begroting_Willianne_Patrick_PRO_v2.xlsx"

# ── App meta ───────────────────────────────────────────────────────────────
APP_CONFIG = {
    "title":         "🏗️ Hofakkers 44 – Bob de Bouwer SaaS",
    "icon":          "🏗️",
    "layout":        "wide",
    "sidebar_state": "expanded",
}

# ── Kleuren ────────────────────────────────────────────────────────────────
COLORS = {
    "primary":    "#FFD700",   # Geel
    "secondary":  "#FF8C00",   # Oranje
    "accent":     "#1A1A2E",   # Antraciet-donker
    "surface":    "#FFFFFF",
    "background": "#FFFBEB",
    "muted":      "#6B7280",
    "success":    "#10B981",
    "warning":    "#F59E0B",
    "error":      "#EF4444",
    "info":       "#3B82F6",
}

PLOTLY_COLORS = [
    "#FFD700", "#FF8C00", "#FFA500", "#FFB347",
    "#FFDA79", "#FFC300", "#FF6B35", "#F7931E",
    "#FDD835", "#FFCA28",
]

# ── Kamer emoji mapping ────────────────────────────────────────────────────
KAMER_EMOJIS = {
    "Woonkamer":  "🛋️",
    "Keuken":     "🍳",
    "Badkamer":   "🛁",
    "Slaapkamer": "🛏️",
    "Hal":        "🚪",
    "Tuin":       "🌳",
    "Garage":     "🚗",
    "Zolder":     "🏠",
    "Kelder":     "🏚️",
    "Algemeen":   "🏗️",
}

DEFAULT_ROOMS = [
    "Woonkamer", "Keuken", "Badkamer", "Slaapkamer",
    "Hal", "Tuin", "Garage", "Zolder", "Kelder", "Algemeen",
]

# ── Statussen ──────────────────────────────────────────────────────────────
TASK_STATUSES = ["Todo", "Bezig", "Gereed"]
WISH_STATUSES = ["Idee", "Gepland", "Gerealiseerd"]
PRIORITEITEN  = ["Laag", "Middel", "Hoog"]
BUDGET_CATEGORIES = [
    "Materialen", "Arbeid", "Keuken", "Sanitair", "Tegels",
    "Verlichting", "Vloer", "Schilderwerk", "Overig",
]
EENHEDEN = ["st", "m2", "m", "container", "uur", "set", "kg"]

# ── Verbouwing & Inboedel Categorieën ──────────────────────────────────────
VERB_CATS = [
    "Uitbouw",
    "Vloeren",
    "Keuken",
    "Sanitair",
    "Schilderwerk",
    "Elektro",
    "Verlichting",
    "Tegels",
    "Reserve",
    "Overig",
]

INBOEDEL_CATS = [
    "Woonkamer",
    "Keuken",
    "Badkamer",
    "Slaapkamer",
    "Hal",
    "Entree",
    "Overig",
]

# ── Status emoji / kleur ───────────────────────────────────────────────────
STATUS_EMOJI = {
    "Todo":          "⚪",
    "Bezig":         "🟡",
    "Gereed":        "🟢",
    "Idee":          "💡",
    "Gepland":       "📋",
    "Gerealiseerd":  "✅",
    "Laag":          "🟢",
    "Middel":        "🟡",
    "Hoog":          "🔴",
}

STATUS_COLORS = {
    "Todo":          "#6B7280",
    "Bezig":         "#F59E0B",
    "Gereed":        "#10B981",
    "Idee":          "#3B82F6",
    "Gepland":       "#8B5CF6",
    "Gerealiseerd":  "#10B981",
}

# ── CSS Animaties & Bob de Bouwer Styling ──────────────────────────────────
CSS_STYLES = """
<style>
/* ── Root & body ── */
:root {
    --primary:   #FFD700;
    --secondary: #FF8C00;
    --accent:    #1A1A2E;
    --radius:    16px;
    --shadow:    0 8px 32px rgba(0,0,0,0.12);
    --shadow-lg: 0 16px 48px rgba(0,0,0,0.18);
}

html, body, [class*="css"] {
    font-family: 'Inter', 'Segoe UI', sans-serif;
}

.stApp {
    background: linear-gradient(135deg, #FFFBEB 0%, #FFF3C4 50%, #FFFBEB 100%);
    min-height: 100vh;
}

/* ── Sidebar ── */
[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #1A1A2E 0%, #16213E 60%, #0F3460 100%) !important;
    border-right: 3px solid #FFD700;
}
[data-testid="stSidebar"] * { color: #F1F1F1 !important; }
[data-testid="stSidebar"] h1,
[data-testid="stSidebar"] h2,
[data-testid="stSidebar"] h3 { color: #FFD700 !important; }
[data-testid="stSidebar"] .stMetric label { color: #FFD700 !important; font-weight: 600; }
[data-testid="stSidebar"] .stMetric [data-testid="stMetricValue"] { color: #FFFFFF !important; font-size: 1.3rem !important; }
[data-testid="stSidebar"] hr { border-color: rgba(255,215,0,0.3) !important; }

/* ── Header bar ── */
.bdb-header {
    background: linear-gradient(90deg, #FFD700, #FF8C00);
    border-radius: 20px;
    padding: 24px 32px;
    margin-bottom: 24px;
    box-shadow: var(--shadow-lg);
    position: relative;
    overflow: hidden;
}
.bdb-header::before {
    content: '';
    position: absolute; top: -50%; right: -10%;
    width: 300px; height: 300px;
    background: rgba(255,255,255,0.1);
    border-radius: 50%;
}
.bdb-header h1 { color: #1A1A2E !important; margin: 0; font-size: 2rem; font-weight: 800; }
.bdb-header p  { color: rgba(26,26,46,0.75) !important; margin: 0; font-size: 1rem; }

/* ── KPI Metric Cards ── */
.kpi-card {
    background: #FFFFFF;
    border-radius: var(--radius);
    padding: 20px 24px;
    border-left: 5px solid var(--primary);
    box-shadow: var(--shadow);
    transition: transform 0.2s ease, box-shadow 0.2s ease;
    cursor: default;
}
.kpi-card:hover { transform: translateY(-4px); box-shadow: var(--shadow-lg); }
.kpi-card .kpi-label { font-size: 0.8rem; font-weight: 600; text-transform: uppercase; letter-spacing: 0.08em; color: #6B7280; margin-bottom: 6px; }
.kpi-card .kpi-value { font-size: 1.9rem; font-weight: 800; color: #1A1A2E; line-height: 1; }
.kpi-card .kpi-delta { font-size: 0.85rem; color: #10B981; margin-top: 4px; font-weight: 600; }
.kpi-card.danger  { border-left-color: #EF4444; }
.kpi-card.danger .kpi-value { color: #EF4444; }
.kpi-card.warning { border-left-color: #F59E0B; }
.kpi-card.success { border-left-color: #10B981; }

/* ── Tegel / navigatiekaart ── */
.tegel-card {
    background: #FFFFFF;
    border-radius: 20px;
    padding: 28px;
    border: 2px solid transparent;
    box-shadow: var(--shadow);
    transition: all 0.25s ease;
    text-decoration: none !important;
    display: block;
    cursor: pointer;
    position: relative;
    overflow: hidden;
}
.tegel-card::after {
    content: '';
    position: absolute; bottom: 0; left: 0; right: 0; height: 4px;
    background: linear-gradient(90deg, #FFD700, #FF8C00);
    transform: scaleX(0); transform-origin: left;
    transition: transform 0.3s ease;
}
.tegel-card:hover { transform: translateY(-6px); box-shadow: var(--shadow-lg); border-color: #FFD700; }
.tegel-card:hover::after { transform: scaleX(1); }
.tegel-card .tegel-emoji { font-size: 2.5rem; margin-bottom: 12px; display: block; }
.tegel-card h3 { color: #1A1A2E; font-size: 1.1rem; font-weight: 700; margin: 0 0 6px 0; }
.tegel-card p  { color: #6B7280; font-size: 0.85rem; margin: 0; line-height: 1.5; }
.tegel-card .tegel-budget { margin-top: 14px; padding-top: 14px; border-top: 1px solid #F3F4F6; font-size: 0.85rem; color: #374151; font-weight: 600; }

/* ── Voortgangsbalk ── */
.progress-wrap { background: #F3F4F6; border-radius: 999px; height: 10px; overflow: hidden; margin: 8px 0; }
.progress-fill {
    height: 100%;
    border-radius: 999px;
    background: linear-gradient(90deg, #FFD700, #FF8C00);
    transition: width 0.6s cubic-bezier(0.34,1.56,0.64,1);
}
.progress-fill.danger  { background: linear-gradient(90deg, #EF4444, #DC2626); }
.progress-fill.success { background: linear-gradient(90deg, #10B981, #059669); }
.progress-label { display: flex; justify-content: space-between; font-size: 0.82rem; color: #6B7280; margin-bottom: 4px; font-weight: 500; }

/* ── Sectie container ── */
.section-box {
    background: #FFFFFF;
    border-radius: var(--radius);
    padding: 24px;
    box-shadow: var(--shadow);
    margin-bottom: 16px;
    border: 1px solid #F3F4F6;
}

/* ── Status badges ── */
.badge {
    display: inline-block;
    padding: 3px 10px;
    border-radius: 999px;
    font-size: 0.75rem;
    font-weight: 600;
    letter-spacing: 0.04em;
}
.badge-todo    { background: #F3F4F6; color: #374151; }
.badge-bezig   { background: #FEF3C7; color: #92400E; }
.badge-gereed  { background: #D1FAE5; color: #065F46; }
.badge-idee    { background: #DBEAFE; color: #1E40AF; }
.badge-gepland { background: #EDE9FE; color: #4C1D95; }
.badge-gerealiseerd { background: #D1FAE5; color: #065F46; }

/* ── Animaties ── */
@keyframes slide-in {
    from { opacity: 0; transform: translateY(24px); }
    to   { opacity: 1; transform: translateY(0); }
}
.animate-in { animation: slide-in 0.4s ease forwards; }

@keyframes pulse-yellow {
    0%, 100% { box-shadow: 0 0 0 0 rgba(255,215,0,0.4); }
    50%       { box-shadow: 0 0 0 12px rgba(255,215,0,0); }
}
.pulse { animation: pulse-yellow 2s infinite; }

/* ── Tabs styling ── */
.stTabs [data-baseweb="tab-list"] {
    background: #F9FAFB;
    border-radius: 12px;
    padding: 4px;
    gap: 4px;
}
.stTabs [data-baseweb="tab"] {
    border-radius: 8px;
    font-weight: 600;
    color: #6B7280;
    transition: all 0.2s;
}
.stTabs [aria-selected="true"] {
    background: linear-gradient(90deg, #FFD700, #FF8C00) !important;
    color: #1A1A2E !important;
}

/* ── Buttons ── */
.stButton > button {
    border-radius: 10px;
    font-weight: 600;
    transition: all 0.2s ease;
}
.stButton > button[kind="primary"] {
    background: linear-gradient(90deg, #FFD700, #FF8C00);
    color: #1A1A2E;
    border: none;
}
.stButton > button[kind="primary"]:hover { transform: translateY(-2px); box-shadow: 0 6px 20px rgba(255,140,0,0.4); }

/* ── Bon scanner card ── */
.bon-card {
    background: linear-gradient(135deg, #1A1A2E, #0F3460);
    border-radius: 20px;
    padding: 28px;
    color: #FFFFFF;
    box-shadow: var(--shadow-lg);
    border: 1px solid rgba(255,215,0,0.2);
}
.bon-card h3 { color: #FFD700 !important; }

/* ── Alerts ── */
.alert-success { background: #D1FAE5; border-left: 4px solid #10B981; border-radius: 8px; padding: 12px 16px; color: #065F46; margin: 8px 0; }
.alert-warning { background: #FEF3C7; border-left: 4px solid #F59E0B; border-radius: 8px; padding: 12px 16px; color: #92400E; margin: 8px 0; }
.alert-error   { background: #FEE2E2; border-left: 4px solid #EF4444; border-radius: 8px; padding: 12px 16px; color: #991B1B; margin: 8px 0; }

/* ── DataEditor tweaks ── */
.stDataEditor { border-radius: 12px; overflow: hidden; }

/* ── Scroll animation ── */
* { scroll-behavior: smooth; }
</style>
"""
