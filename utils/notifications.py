"""
utils/notifications.py  –  Hofakkers 44  v4.0

Proactieve notificatie-engine.
Berekent alle relevante alerts op basis van session_state en toont ze
consistent op elke pagina. Nooit meer "alleen als je ernaar navigeert".

Categorieën:
  🔴 KRITIEK  – over budget, negatieve buffer
  🟡 WAARSCHUWING – >80% benut, naderende deadline
  🔵 INFO     – neutrale updates, suggesties
  🟢 SUCCES   – mijlpalen bereikt
"""
import streamlit as st
import pandas as pd
from datetime import date, timedelta

from utils.config import YNAB_WARN_PCT, YNAB_CRIT_PCT


# ── Types ──────────────────────────────────────────────────────────────────

KRITIEK    = "red"
WARN       = "warn"
INFO       = "blu"
SUCCES     = "grn"


def _sf(v) -> float:
    try:
        return float(str(v or 0).replace(",",".").replace("€","").strip())
    except (TypeError, ValueError):
        return 0.0


# ── Bereken alle actieve notificaties ─────────────────────────────────────

def get_notifications() -> list[dict]:
    """
    Retourneert gesorteerde lijst van notificaties:
    [{level, titel, tekst, pagina, emoji}]
    Kritiek eerst, daarna warn, dan info/succes.
    """
    msgs = []

    # ── 1. Budget-overschrijdingen per envelope ──
    try:
        from utils.state import calc_ynab_envelopes, calc_maand_totalen, calc_spaargeld
        ynab = calc_ynab_envelopes()

        # Vrije buffer
        if ynab["vrij"] < 0:
            msgs.append({
                "level": KRITIEK,
                "emoji": "🚨",
                "titel": "Project over budget!",
                "tekst": f"De totale toewijzing (€ {ynab['toegewezen']:,.0f}) "
                         f"overschrijdt het beschikbare vermogen (€ {ynab['totaal_inleg']:,.0f}) "
                         f"met € {abs(ynab['vrij']):,.0f}.",
                "pagina": "Dashboard",
            })
        elif ynab["vrij"] < 5000:
            msgs.append({
                "level": WARN,
                "emoji": "⚠️",
                "titel": "Lage vrije buffer",
                "tekst": f"Nog slechts € {ynab['vrij']:,.0f} vrij te verdelen. "
                         "Overweeg de reservepost te verhogen.",
                "pagina": "Dashboard",
            })

        # Per envelope: over budget of waarschuwing
        for env in ynab["envelopes"]:
            naam   = env["naam"]
            type_  = env["type"].title()
            pct    = env["pct"]
            real   = env["gerealiseerd"]
            begroot = env["begroot"]
            if pct > YNAB_CRIT_PCT:
                msgs.append({
                    "level": KRITIEK,
                    "emoji": "🔴",
                    "titel": f"{naam} over budget",
                    "tekst": f"{type_}: € {real:,.0f} besteed van € {begroot:,.0f} begroot "
                             f"({pct:.0f}% — € {real-begroot:,.0f} te veel).",
                    "pagina": type_,
                })
            elif pct >= YNAB_WARN_PCT:
                msgs.append({
                    "level": WARN,
                    "emoji": "🟡",
                    "titel": f"{naam} bijna vol ({pct:.0f}%)",
                    "tekst": f"{type_}: € {env['beschikbaar']:,.0f} resterend van € {begroot:,.0f}.",
                    "pagina": type_,
                })
    except Exception:
        pass

    # ── 2. Maandelijkse cashflow ──
    try:
        mt = calc_maand_totalen()
        ink = mt.get("inkomen", 0)
        if ink > 0:
            pct_uit = mt.get("totaal_uitgaven", 0) / ink * 100
            ruimte  = mt.get("ruimte", 0)
            if ruimte < 0:
                msgs.append({
                    "level": KRITIEK,
                    "emoji": "💸",
                    "titel": "Maandlasten overschrijden inkomen",
                    "tekst": f"Maanduitgaven (€ {mt['totaal_uitgaven']:,.0f}) > "
                             f"inkomen (€ {ink:,.0f}). Tekort: € {abs(ruimte):,.0f}/maand.",
                    "pagina": "Cashflow",
                })
            elif pct_uit > 85:
                msgs.append({
                    "level": WARN,
                    "emoji": "💳",
                    "titel": f"Hoge maandlastenratio ({pct_uit:.0f}%)",
                    "tekst": f"Slechts € {ruimte:,.0f}/maand vrij. "
                             "Onvoldoende buffer voor onverwachte kosten.",
                    "pagina": "Cashflow",
                })
    except Exception:
        pass

    # ── 3. Planning deadlines (uit session_state) ──
    try:
        planning = st.session_state.get("planning", [])
        today    = date.today()
        warn_horizon = today + timedelta(days=14)

        for stap in planning:
            dl_str = str(stap.get("Deadline", "") or "")
            status = str(stap.get("Status", ""))
            naam   = str(stap.get("Taak", ""))
            if not dl_str or status == "Gereed":
                continue
            try:
                dl = date.fromisoformat(dl_str)
                if dl < today:
                    msgs.append({
                        "level": KRITIEK,
                        "emoji": "📅",
                        "titel": f"Deadline verstreken: {naam}",
                        "tekst": f"Was gepland voor {dl.strftime('%d-%m-%Y')} "
                                 f"({(today-dl).days} dagen geleden). Status: {status}.",
                        "pagina": "Planning",
                    })
                elif dl <= warn_horizon:
                    msgs.append({
                        "level": WARN,
                        "emoji": "🗓️",
                        "titel": f"Deadline nadert: {naam}",
                        "tekst": f"Gepland voor {dl.strftime('%d-%m-%Y')} "
                                 f"(nog {(dl-today).days} dagen). Status: {status}.",
                        "pagina": "Planning",
                    })
            except ValueError:
                pass
    except Exception:
        pass

    # ── 4. Verbouwing voortgang: succes-mijlpalen ──
    try:
        planning = st.session_state.get("planning", [])
        if planning:
            gereed   = sum(1 for p in planning if p.get("Status") == "Gereed")
            totaal_p = len(planning)
            pct_done = gereed / totaal_p * 100 if totaal_p else 0

            if gereed == totaal_p and totaal_p > 0:
                msgs.append({
                    "level": SUCCES,
                    "emoji": "🎉",
                    "titel": "Alle taken gereed!",
                    "tekst": f"Alle {totaal_p} planningstaken zijn afgerond. Proficiat!",
                    "pagina": "Planning",
                })
            elif pct_done >= 50 and pct_done < 51:  # eenmalig bij 50%
                msgs.append({
                    "level": SUCCES,
                    "emoji": "🏆",
                    "titel": "50% van de planning gereed!",
                    "tekst": f"{gereed} van de {totaal_p} taken afgerond. "
                             "Halverwege!",
                    "pagina": "Planning",
                })
    except Exception:
        pass

    # ── 5. Lege begrotingen ──
    try:
        verb = st.session_state.get("verbouwing", pd.DataFrame())
        if verb.empty:
            msgs.append({
                "level": INFO,
                "emoji": "📋",
                "titel": "Verbouwingsbegroting leeg",
                "tekst": "Nog geen verbouwingsposten ingevuld. "
                         "Ga naar 🔨 Verbouwing → Begroting Bewerken.",
                "pagina": "Verbouwing",
            })
        inbo = st.session_state.get("inboedel", pd.DataFrame())
        if inbo.empty:
            msgs.append({
                "level": INFO,
                "emoji": "📋",
                "titel": "Inboedelbegroting leeg",
                "tekst": "Nog geen inboedelposten ingevuld. "
                         "Ga naar 🛋️ Inboedel → Begroting Bewerken.",
                "pagina": "Inboedel",
            })
    except Exception:
        pass

    # ── Sortering: kritiek → warn → info → succes ──
    order = {KRITIEK: 0, WARN: 1, INFO: 2, SUCCES: 3}
    msgs.sort(key=lambda x: order.get(x["level"], 99))
    return msgs


def get_notification_counts() -> dict:
    """Snelle teller voor sidebar-badge."""
    msgs = get_notifications()
    return {
        "kritiek": sum(1 for m in msgs if m["level"] == KRITIEK),
        "warn":    sum(1 for m in msgs if m["level"] == WARN),
        "info":    sum(1 for m in msgs if m["level"] == INFO),
        "succes":  sum(1 for m in msgs if m["level"] == SUCCES),
        "totaal":  len(msgs),
    }


# ── Render helpers ─────────────────────────────────────────────────────────

def render_notification_bar(max_visible: int = 3,
                             filter_page: str = "") -> None:
    """
    Toon notificaties als compacte alert-balk.
    filter_page: toon alleen berichten voor deze pagina (+ algemeen).
    """
    msgs = get_notifications()
    if filter_page:
        msgs = [m for m in msgs
                if m.get("pagina", "") in (filter_page, "Dashboard", "")]

    if not msgs:
        return

    # Kritieke berichten altijd allemaal tonen
    kritiek = [m for m in msgs if m["level"] == KRITIEK]
    rest    = [m for m in msgs if m["level"] != KRITIEK][:max(0, max_visible - len(kritiek))]
    visible = kritiek + rest
    hidden  = len(msgs) - len(visible)

    for m in visible:
        bg   = {"red":"#FEE2E2","warn":"#FEF3C7","blu":"#DBEAFE","grn":"#D1FAE5"}.get(m["level"],"#F3F4F6")
        bdr  = {"red":"#EF4444","warn":"#F59E0B","blu":"#3B82F6","grn":"#10B981"}.get(m["level"],"#6B7280")
        color= {"red":"#991B1B","warn":"#92400E","blu":"#1E40AF","grn":"#065F46"}.get(m["level"],"#374151")
        st.markdown(f"""
        <div style='background:{bg};border-left:4px solid {bdr};border-radius:8px;
                    padding:9px 14px;margin:4px 0;font-size:.82rem;color:{color};'>
          <strong>{m["emoji"]} {m["titel"]}</strong> — {m["tekst"]}
        </div>""", unsafe_allow_html=True)

    if hidden > 0:
        st.caption(f"+ {hidden} meer melding(en) — zie 🔔 Meldingen pagina voor volledig overzicht.")


def render_full_notification_panel() -> None:
    """Volledige notificatie-pagina met filtering."""
    msgs = get_notifications()
    if not msgs:
        st.success("✅ Geen actieve meldingen. Alles ziet er goed uit!")
        return

    counts = get_notification_counts()
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("🔴 Kritiek",     counts["kritiek"])
    c2.metric("🟡 Waarschuwing",counts["warn"])
    c3.metric("🔵 Info",        counts["info"])
    c4.metric("🟢 Succes",      counts["succes"])

    st.markdown("---")

    tabs = st.tabs(["Alles", "🔴 Kritiek", "🟡 Waarschuwing", "🔵 Info", "🟢 Succes"])

    def _show(filtered):
        if not filtered:
            st.info("Geen meldingen in deze categorie.")
            return
        for m in filtered:
            bg   = {"red":"#FEE2E2","warn":"#FEF3C7","blu":"#DBEAFE","grn":"#D1FAE5"}.get(m["level"],"#F3F4F6")
            bdr  = {"red":"#EF4444","warn":"#F59E0B","blu":"#3B82F6","grn":"#10B981"}.get(m["level"],"#6B7280")
            color= {"red":"#991B1B","warn":"#92400E","blu":"#1E40AF","grn":"#065F46"}.get(m["level"],"#374151")
            page_badge = f" <span style='background:rgba(0,0,0,.08);padding:1px 6px;border-radius:4px;font-size:.7rem;'>📍 {m.get('pagina','')}</span>" if m.get("pagina") else ""
            st.markdown(f"""
            <div style='background:{bg};border-left:4px solid {bdr};border-radius:10px;
                        padding:12px 16px;margin:6px 0;color:{color};'>
              <div style='font-weight:700;font-size:.88rem;'>{m["emoji"]} {m["titel"]}{page_badge}</div>
              <div style='font-size:.82rem;margin-top:3px;'>{m["tekst"]}</div>
            </div>""", unsafe_allow_html=True)

    with tabs[0]: _show(msgs)
    with tabs[1]: _show([m for m in msgs if m["level"] == KRITIEK])
    with tabs[2]: _show([m for m in msgs if m["level"] == WARN])
    with tabs[3]: _show([m for m in msgs if m["level"] == INFO])
    with tabs[4]: _show([m for m in msgs if m["level"] == SUCCES])
