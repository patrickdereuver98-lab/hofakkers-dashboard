"""
utils/config.py  –  Hofakkers 44  v4.0
Mobile-first CSS + planning + export + notificatie constanten.
"""
from pathlib import Path

DATA_DIR    = Path(__file__).parent.parent / "data"
EXCEL_FILE  = DATA_DIR / "Begroting_Willianne_Patrick_PRO_v2.xlsx"
BACKUP_DIR  = DATA_DIR / "backups"
BACKUP_DIR.mkdir(parents=True, exist_ok=True)
MAX_BACKUPS = 10

APP_CONFIG = {"title":"🏠 Hofakkers 44","icon":"🏠","layout":"wide","sidebar_state":"expanded"}

C_GEEL="#FFD700";C_ORANJE="#FF8C00";C_ANTRAC="#1A1A2E"
C_GROEN="#10B981";C_ROOD="#EF4444";C_BLAUW="#3B82F6"
C_GRIJS="#6B7280";C_GEEL_LT="#FFFBEB";C_WARN="#F59E0B"

CHART_COLORS=["#FFD700","#FF8C00","#FFA500","#FFB347",
              "#10B981","#3B82F6","#8B5CF6","#EC4899",
              "#14B8A6","#F59E0B","#FFDA79","#FFC300"]
PLOTLY_COLORS=CHART_COLORS

SH_DASHBOARD="Dashboard PRO";SH_MAAND="Maandbegroting"
SH_SPAARGELD="Spaargeld + verbouwing";SH_VERBOUWING="Verbouwing begroting"
SH_INBOEDEL="Inboedel begroting";SH_SPAREN="Sparen & Beleggen"
SH_HYPOTHEEK="Hypotheek";SH_KOSTEN="Kosten";SH_BUFFER="Buffer"

VERB_CATS=["Uitbouw","Vloeren & vloerverwarming","Keuken met kookeiland",
           "Schilder- en behangwerk binnen","Badkamer & toilet",
           "Overig","Reserve","Overig & reserve"]
INBOEDEL_CATS=["Woonkamer","Eethoek","Keuken","Slaapkamer","Zolder / Logeerkamer",
               "Werkkamer","Badkamer","Toilet","Wasruimte","Schoonmaak","Overig"]
EENHEDEN=["stuks","m²","m¹","post","set","uur","st","m2","m"]

YNAB_WARN_PCT=80;YNAB_CRIT_PCT=100
FISCAAL_TYPES=["Verbetering","Onderhoud","Neutraal"]

ROOM_STATUSES={"Planningsfase":"🎨","In uitvoering":"🚧","Klaar":"✅","On hold":"⏸️"}
ROOM_STATUS_COLORS={"Planningsfase":"#8B5CF6","In uitvoering":"#F59E0B","Klaar":"#10B981","On hold":"#6B7280"}
KAMER_EMOJIS={"Uitbouw":"🏗️","Vloeren & vloerverwarming":"🪵","Keuken met kookeiland":"🍳",
              "Schilder- en behangwerk binnen":"🎨","Badkamer & toilet":"🛁",
              "Overig & reserve":"📦","Overig":"📦","Reserve":"🛡️","Woonkamer":"🛋️",
              "Eethoek":"🍽️","Keuken":"🍳","Slaapkamer":"🛏️","Badkamer":"🛁",
              "Toilet":"🚽","Wasruimte":"🫧","Werkkamer":"💼",
              "Zolder / Logeerkamer":"🏠","Schoonmaak":"🧹"}

# ── CSS v4.0 — Mobile-first ────────────────────────────────────────────────
CSS_STYLES = """
<style>
/* ── Reset & Variables ── */
:root{
  --geel:#FFD700;--oranje:#FF8C00;--antrac:#1A1A2E;
  --groen:#10B981;--rood:#EF4444;--blauw:#3B82F6;
  --r:12px;--sh:0 2px 12px rgba(0,0,0,.07);--sh-lg:0 8px 32px rgba(0,0,0,.12);
}
html,body,[class*="css"]{font-family:'Inter','Segoe UI',sans-serif;}
.stApp{background:linear-gradient(155deg,#FFFBEB 0%,#FFF8DC 50%,#FFFBEB 100%);}

/* ── Sidebar ── */
[data-testid="stSidebar"]{
  background:linear-gradient(180deg,#1A1A2E 0%,#16213E 55%,#0F3460 100%) !important;
  border-right:3px solid #FFD700;}
[data-testid="stSidebar"] *{color:#F1F1F1 !important;}
[data-testid="stSidebar"] h1,[data-testid="stSidebar"] h2,
[data-testid="stSidebar"] h3,[data-testid="stSidebar"] h4{color:#FFD700 !important;}
[data-testid="stSidebar"] .stMetric label{color:#FFD700 !important;font-weight:600;}
[data-testid="stSidebar"] .stMetric [data-testid="stMetricValue"]{color:#fff !important;font-size:1.05rem !important;}
[data-testid="stSidebar"] hr{border-color:rgba(255,215,0,.2) !important;}
[data-testid="stSidebar"] .stButton>button{
  background:rgba(255,215,0,.12);color:#FFD700 !important;
  border:1px solid rgba(255,215,0,.3);font-weight:600;}

/* ── Page header ── */
.hdr{background:linear-gradient(100deg,#FFD700,#FF8C00);border-radius:14px;
  padding:16px 22px;margin-bottom:14px;box-shadow:var(--sh-lg);position:relative;overflow:hidden;}
.hdr::before{content:'';position:absolute;top:-40%;right:-8%;width:180px;height:180px;
  background:rgba(255,255,255,.1);border-radius:50%;}
.hdr h1{color:#1A1A2E !important;margin:0;font-weight:800;font-size:clamp(1.2rem,3vw,1.75rem);}
.hdr p{color:rgba(28,28,46,.72) !important;margin:3px 0 0;font-size:clamp(.75rem,2vw,.88rem);}

/* ── Hero KPI ── */
.hero{background:linear-gradient(135deg,#fff 0%,#FFFBEB 100%);
  border-radius:var(--r);padding:14px 16px;
  border:2px solid rgba(255,215,0,.3);box-shadow:var(--sh-lg);position:relative;overflow:hidden;}
.hero .hero-lbl{font-size:.68rem;font-weight:700;text-transform:uppercase;
  letter-spacing:.07em;color:#6B7280;margin-bottom:2px;}
.hero .hero-val{font-size:clamp(1.3rem,4vw,1.85rem);font-weight:900;color:#1A1A2E;line-height:1;}
.hero .hero-sub{font-size:.72rem;margin-top:3px;font-weight:600;color:#6B7280;}
.hero.grn .hero-val{color:#059669;}
.hero.red .hero-val{color:#DC2626;}
.hero.warn .hero-val{color:#D97706;}

/* ── KPI card ── */
.kpi{background:#fff;border-radius:var(--r);padding:12px 16px;
  border-left:4px solid #FFD700;box-shadow:var(--sh);transition:transform .18s;margin-bottom:2px;}
.kpi:hover{transform:translateY(-2px);box-shadow:var(--sh-lg);}
.kpi .lbl{font-size:.68rem;font-weight:700;text-transform:uppercase;
  letter-spacing:.07em;color:#6B7280;margin-bottom:3px;}
.kpi .val{font-size:clamp(1.1rem,3vw,1.55rem);font-weight:800;color:#1A1A2E;line-height:1.05;}
.kpi .sub{font-size:.7rem;margin-top:2px;font-weight:600;}
.kpi.grn{border-left-color:#10B981;}.kpi.grn .val,.kpi.grn .sub{color:#10B981;}
.kpi.red{border-left-color:#EF4444;}.kpi.red .val,.kpi.red .sub{color:#EF4444;}
.kpi.blu{border-left-color:#3B82F6;}.kpi.blu .val{color:#3B82F6;}
.kpi.warn{border-left-color:#F59E0B;}.kpi.warn .val{color:#F59E0B;}
.kpi.neu{border-left-color:#FFD700;}

/* ── Stat strip ── */
.stat-strip{background:#fff;border-radius:10px;padding:10px 12px;
  box-shadow:0 2px 8px rgba(0,0,0,.05);text-align:center;transition:transform .15s;}
.stat-strip:hover{transform:translateY(-2px);}
.stat-strip .ss-emoji{font-size:1.3rem;display:block;margin-bottom:2px;}
.stat-strip .ss-val{font-size:clamp(.85rem,2.5vw,1.05rem);font-weight:800;color:#1A1A2E;line-height:1;}
.stat-strip .ss-lbl{font-size:.6rem;color:#6B7280;text-transform:uppercase;letter-spacing:.05em;margin-top:2px;}

/* ── Progress bar ── */
.pgwrap{margin:4px 0 10px;}
.pglbl{display:flex;justify-content:space-between;font-size:.72rem;
  color:#6B7280;font-weight:500;margin-bottom:2px;}
.pgbar{background:#F3F4F6;border-radius:999px;height:8px;overflow:hidden;}
.pgfill{height:100%;border-radius:999px;
  background:linear-gradient(90deg,#FFD700,#FF8C00);
  transition:width .5s cubic-bezier(.34,1.56,.64,1);}
.pgfill.grn{background:linear-gradient(90deg,#10B981,#059669);}
.pgfill.warn{background:linear-gradient(90deg,#F59E0B,#D97706);}
.pgfill.red{background:linear-gradient(90deg,#EF4444,#DC2626);}

/* ── Notion kamerkaart ── */
.room-card{background:#fff;border-radius:14px;padding:14px;
  box-shadow:var(--sh);border:2px solid transparent;
  transition:all .22s ease;position:relative;overflow:hidden;}
.room-card::after{content:'';position:absolute;bottom:0;left:0;right:0;height:3px;
  background:linear-gradient(90deg,#FFD700,#FF8C00);
  transform:scaleX(0);transform-origin:left;transition:transform .28s ease;}
.room-card:hover{transform:translateY(-2px);box-shadow:var(--sh-lg);border-color:#FFD700;}
.room-card:hover::after{transform:scaleX(1);}
.room-card .rc-title{font-size:.9rem;font-weight:700;color:#1A1A2E;margin:4px 0 3px;}
.room-card .rc-emoji{font-size:1.6rem;display:block;margin-bottom:1px;}

/* ── Status badge ── */
.badge{display:inline-block;padding:2px 7px;border-radius:999px;
  font-size:.63rem;font-weight:700;letter-spacing:.04em;margin-bottom:5px;}
.badge-plan{background:#EDE9FE;color:#5B21B6;}
.badge-wip{background:#FEF3C7;color:#92400E;}
.badge-done{background:#D1FAE5;color:#065F46;}
.badge-hold{background:#F3F4F6;color:#374151;}

/* ── YNAB envelope row — MOBILE FIX ── */
.env-row{display:flex;align-items:center;gap:6px;padding:6px 0;
  border-bottom:1px solid #F3F4F6;flex-wrap:wrap;}
/* MOBILE: naam op volle breedte, bar + bedrag op tweede rij */
.env-name{font-size:.78rem;font-weight:600;color:#374151;
  min-width:0;  /* FIX: was 200px, brak op mobiel */
  flex:1 1 120px;word-break:break-word;}
.env-bar{flex:2 1 80px;min-width:60px;background:#F3F4F6;border-radius:999px;height:6px;overflow:hidden;}
.env-fill{height:100%;border-radius:999px;background:linear-gradient(90deg,#10B981,#059669);}
.env-fill.warn{background:linear-gradient(90deg,#F59E0B,#D97706);}
.env-fill.red{background:linear-gradient(90deg,#EF4444,#DC2626);}
.env-amt{font-size:.75rem;font-weight:700;white-space:nowrap;flex-shrink:0;}
.env-amt.grn{color:#10B981;}.env-amt.warn{color:#F59E0B;}.env-amt.red{color:#EF4444;}

/* ── Planningskaart ── */
.plan-card{background:#fff;border-radius:12px;padding:12px 14px;
  box-shadow:var(--sh);margin-bottom:8px;
  border-left:4px solid #FFD700;position:relative;transition:all .18s ease;}
.plan-card:hover{box-shadow:var(--sh-lg);transform:translateY(-1px);}
.plan-card.status-gereed{border-left-color:#10B981;opacity:.85;}
.plan-card.status-uitvoering{border-left-color:#F59E0B;}
.plan-card.status-wacht{border-left-color:#8B5CF6;}
.plan-card.status-onhold{border-left-color:#EF4444;}
.plan-card .pc-title{font-size:.9rem;font-weight:700;color:#1A1A2E;margin-bottom:3px;}
.plan-card .pc-meta{font-size:.72rem;color:#6B7280;display:flex;flex-wrap:wrap;gap:8px;}
.plan-card .pc-badge{font-size:.64rem;font-weight:700;padding:1px 7px;border-radius:999px;}

/* ── Section divider ── */
.sec-div{display:flex;align-items:center;gap:8px;margin:14px 0 10px;}
.sec-div .sec-emoji{font-size:1.3rem;}
.sec-div .sec-title{font-size:1rem;font-weight:700;color:#1A1A2E;}
.sec-div .sec-line{flex:1;height:2px;background:linear-gradient(90deg,rgba(255,215,0,.4) 0%,transparent 100%);}

/* ── Tabs ── */
.stTabs [data-baseweb="tab-list"]{background:#F9FAFB;border-radius:10px;padding:3px;gap:2px;}
.stTabs [data-baseweb="tab"]{border-radius:7px;font-weight:600;color:#6B7280;
  font-size:clamp(.72rem,2vw,.85rem);}
.stTabs [aria-selected="true"]{background:linear-gradient(90deg,#FFD700,#FF8C00) !important;color:#1A1A2E !important;}

/* ── Buttons ── */
.stButton>button[kind="primary"]{
  background:linear-gradient(90deg,#FFD700,#FF8C00);
  color:#1A1A2E;border:none;border-radius:9px;font-weight:700;
  font-size:clamp(.78rem,2vw,.9rem);}
.stButton>button[kind="primary"]:hover{transform:translateY(-2px);box-shadow:0 6px 18px rgba(255,140,0,.35);}
.stButton>button{border-radius:9px;}
.stDataEditor{border-radius:12px;overflow:hidden;}

/* ── Alert ── */
.alrt{border-radius:10px;padding:10px 14px;margin:4px 0;font-size:.8rem;font-weight:500;line-height:1.4;}
.alrt.grn{background:#D1FAE5;border-left:4px solid #10B981;color:#065F46;}
.alrt.warn{background:#FEF3C7;border-left:4px solid #F59E0B;color:#92400E;}
.alrt.red{background:#FEE2E2;border-left:4px solid #EF4444;color:#991B1B;}
.alrt.blu{background:#DBEAFE;border-left:4px solid #3B82F6;color:#1E40AF;}

/* ── Animate ── */
@keyframes fadeup{from{opacity:0;transform:translateY(12px)}to{opacity:1;transform:translateY(0)}}
.ani{animation:fadeup .28s ease forwards;}

/* ── MOBILE RESPONSIVE ── */
@media (max-width: 768px) {
  /* Header kleiner */
  .hdr{padding:12px 16px;border-radius:12px;}
  /* KPI cards: volle breedte op mobiel */
  .kpi{padding:10px 14px;}
  .kpi .val{font-size:1.25rem;}
  /* Hero vals kleiner */
  .hero{padding:12px 14px;}
  .hero .hero-val{font-size:1.5rem;}
  /* Room cards compacter */
  .room-card{padding:12px;}
  /* YNAB rows stacked */
  .env-row{flex-direction:column;align-items:flex-start;gap:4px;}
  .env-name{flex:none;width:100%;}
  .env-bar{width:100%;flex:none;}
  .env-amt{align-self:flex-end;}
  /* Planning cards compacter */
  .plan-card{padding:10px 12px;}
  /* Stat strips kleiner */
  .stat-strip{padding:8px 10px;}
  .stat-strip .ss-emoji{font-size:1.1rem;}
  /* Verberg decoratieve sidebar-elementen die ruimte wegnemen */
  .sec-div .sec-line{display:none;}
  /* Grotere knoppen voor touch */
  .stButton>button{min-height:44px;font-size:.88rem !important;}
}

@media (max-width: 480px) {
  .hdr h1{font-size:1.1rem;}
  .hdr p{font-size:.72rem;}
  .kpi .val{font-size:1.1rem;}
  .hero .hero-val{font-size:1.3rem;}
  .stat-strip .ss-val{font-size:.85rem;}
  /* Envelopes: toon alleen naam + bedrag, verberg bar */
  .env-bar{display:none;}
  /* Plan meta op mobiel: alleen icoon + tekst */
  .plan-card .pc-meta{font-size:.68rem;}
}
</style>
"""
