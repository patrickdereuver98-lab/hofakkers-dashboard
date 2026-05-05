"""
utils/config.py  –  Hofakkers 44
Centrale configuratie. Pas hier kleuren/paden aan – werkt direct door in de hele app.
"""
from pathlib import Path

# ── Paden ──────────────────────────────────────────────────────────────────
DATA_DIR   = Path(__file__).parent.parent / "data"
EXCEL_FILE = DATA_DIR / "Begroting_Willianne_Patrick_PRO_v2.xlsx"

# ── App meta ───────────────────────────────────────────────────────────────
APP_CONFIG = {
    "title":         "🏠 Hofakkers 44",
    "icon":          "🏠",
    "layout":        "wide",
    "sidebar_state": "expanded",
}

# ── Kleuren ────────────────────────────────────────────────────────────────
COLORS = {
    "primary":    "#FFD700",
    "secondary":  "#FF8C00",
    "accent":     "#1A1A2E",
    "surface":    "#FFFFFF",
    "background": "#FFFBEB",
    "muted":      "#6B7280",
    "success":    "#10B981",
    "warning":    "#F59E0B",
    "error":      "#EF4444",
    "info":       "#3B82F6",
}

# ── BUG FIX: CHART_COLORS als lijst (was ontbrekend → ImportError in alle pagina's) ──
CHART_COLORS = [
    "#FFD700", "#FF8C00", "#FFA500", "#FFB347",
    "#10B981", "#3B82F6", "#8B5CF6", "#EC4899",
    "#14B8A6", "#F59E0B", "#FFDA79", "#FFC300",
]

# Alias voor backward compat
PLOTLY_COLORS = CHART_COLORS

# ── Excel sheet namen (exact zoals in het bestand) ─────────────────────────
SH_DASHBOARD  = "Dashboard PRO"
SH_MAAND      = "Maandbegroting"
SH_SPAARGELD  = "Spaargeld + verbouwing"
SH_VERBOUWING = "Verbouwing begroting"
SH_INBOEDEL   = "Inboedel begroting"
SH_SPAREN     = "Sparen & Beleggen"
SH_HYPOTHEEK  = "Hypotheek"

# ── Kamer / sectie mapping ─────────────────────────────────────────────────
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

# ── Verbouwing categorieën (exact uit de echte Excel) ─────────────────────
VERB_CATS = [
    "Uitbouw",
    "Vloeren & vloerverwarming",
    "Keuken met kookeiland",
    "Schilder- en behangwerk binnen",
    "Badkamer & toilet",
    "Overig & reserve",
    "Overig",
    "Reserve",
]

# ── Inboedel categorieën (exact uit de echte Excel) ──────────────────────
# BUG FIX: was onjuiste lijst; dit zijn de werkelijke Excel-categorieën
INBOEDEL_CATS = [
    "Woonkamer",
    "Eethoek",
    "Keuken",
    "Slaapkamer",
    "Zolder / Logeerkamer",
    "Werkkamer",
    "Badkamer",
    "Toilet",
    "Wasruimte",
    "Schoonmaak",
    "Overig",
]

EENHEDEN = ["stuks", "m²", "m¹", "post", "set", "uur", "st", "m2", "m"]

# ── Statussen ──────────────────────────────────────────────────────────────
TASK_STATUSES = ["Todo", "Bezig", "Gereed"]
WISH_STATUSES = ["Idee", "Gepland", "Gerealiseerd"]
PRIORITEITEN  = ["Laag", "Middel", "Hoog"]
BUDGET_CATEGORIES = [
    "Materialen", "Arbeid", "Keuken", "Sanitair", "Tegels",
    "Verlichting", "Vloer", "Schilderwerk", "Overig",
]

STATUS_EMOJI = {
    "Todo": "⚪", "Bezig": "🟡", "Gereed": "🟢",
    "Idee": "💡", "Gepland": "📋", "Gerealiseerd": "✅",
    "Laag": "🟢", "Middel": "🟡", "Hoog": "🔴",
}

# ── CSS ────────────────────────────────────────────────────────────────────
CSS_STYLES = """
<style>
:root {
    --primary: #FFD700; --secondary: #FF8C00;
    --accent: #1A1A2E; --radius: 16px;
    --shadow: 0 4px 20px rgba(0,0,0,0.08);
    --shadow-lg: 0 12px 40px rgba(0,0,0,0.14);
}
html,body,[class*="css"]{font-family:'Inter','Segoe UI',sans-serif;}
.stApp{background:linear-gradient(135deg,#FFFBEB 0%,#FFF3C4 50%,#FFFBEB 100%);}

[data-testid="stSidebar"]{
    background:linear-gradient(180deg,#1A1A2E 0%,#16213E 60%,#0F3460 100%) !important;
    border-right:3px solid #FFD700;
}
[data-testid="stSidebar"] *{color:#F1F1F1 !important;}
[data-testid="stSidebar"] h1,[data-testid="stSidebar"] h2,
[data-testid="stSidebar"] h3,[data-testid="stSidebar"] h4{color:#FFD700 !important;}
[data-testid="stSidebar"] .stMetric label{color:#FFD700 !important;font-weight:600;}
[data-testid="stSidebar"] .stMetric [data-testid="stMetricValue"]{color:#fff !important;font-size:1.2rem !important;}
[data-testid="stSidebar"] hr{border-color:rgba(255,215,0,.25) !important;}

.bdb-header{
    background:linear-gradient(100deg,#FFD700,#FF8C00);
    border-radius:20px;padding:22px 30px;margin-bottom:22px;
    box-shadow:var(--shadow-lg);position:relative;overflow:hidden;
}
.bdb-header h1{color:#1A1A2E !important;margin:0;font-size:1.9rem;font-weight:800;}
.bdb-header p{color:rgba(26,26,46,.75) !important;margin:4px 0 0;font-size:.95rem;}

.kpi-card{
    background:#fff;border-radius:var(--radius);padding:18px 22px;
    border-left:5px solid #FFD700;box-shadow:var(--shadow);
    transition:transform .18s,box-shadow .18s;
}
.kpi-card:hover{transform:translateY(-3px);box-shadow:var(--shadow-lg);}
.kpi-card .kpi-label{font-size:.75rem;font-weight:700;text-transform:uppercase;
    letter-spacing:.07em;color:#6B7280;margin-bottom:5px;}
.kpi-card .kpi-value{font-size:1.75rem;font-weight:800;color:#1A1A2E;line-height:1;}
.kpi-card .kpi-delta{font-size:.8rem;color:#10B981;margin-top:3px;font-weight:600;}
.kpi-card.danger{border-left-color:#EF4444;}.kpi-card.danger .kpi-value{color:#EF4444;}
.kpi-card.warning{border-left-color:#F59E0B;}
.kpi-card.success{border-left-color:#10B981;}.kpi-card.success .kpi-value{color:#10B981;}
.kpi-card.blu{border-left-color:#3B82F6;}.kpi-card.blu .kpi-value{color:#3B82F6;}
.kpi-card.grn{border-left-color:#10B981;}.kpi-card.grn .kpi-value{color:#10B981;}
.kpi-card.red{border-left-color:#EF4444;}.kpi-card.red .kpi-value{color:#EF4444;}

.pgwrap{margin:6px 0 14px;}
.pglbl{display:flex;justify-content:space-between;font-size:.78rem;color:#6B7280;font-weight:500;margin-bottom:4px;}
.pgbar{background:#F3F4F6;border-radius:999px;height:10px;overflow:hidden;}
.pgfill{height:100%;border-radius:999px;background:linear-gradient(90deg,#FFD700,#FF8C00);
    transition:width .6s cubic-bezier(.34,1.56,.64,1);}
.pgfill.red{background:linear-gradient(90deg,#EF4444,#DC2626);}
.pgfill.grn{background:linear-gradient(90deg,#10B981,#059669);}

.stTabs [data-baseweb="tab-list"]{background:#F9FAFB;border-radius:12px;padding:4px;gap:4px;}
.stTabs [data-baseweb="tab"]{border-radius:8px;font-weight:600;color:#6B7280;}
.stTabs [aria-selected="true"]{background:linear-gradient(90deg,#FFD700,#FF8C00) !important;color:#1A1A2E !important;}

.stButton>button[kind="primary"]{
    background:linear-gradient(90deg,#FFD700,#FF8C00);
    color:#1A1A2E;border:none;border-radius:9px;font-weight:700;}
.stButton>button[kind="primary"]:hover{transform:translateY(-2px);box-shadow:0 6px 18px rgba(255,140,0,.35);}
.stButton>button{border-radius:9px;}
.stDataEditor{border-radius:12px;overflow:hidden;}

@keyframes fadeup{from{opacity:0;transform:translateY(18px)}to{opacity:1;transform:translateY(0)}}
.animate-in{animation:fadeup .35s ease forwards;}
</style>
"""
