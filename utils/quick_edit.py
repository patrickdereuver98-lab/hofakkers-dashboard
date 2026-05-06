"""
utils/quick_edit.py  –  Hofakkers 44  v6.0

Herbruikbare Quick-Edit engine.
Kern-filosofie: klik → categorie → items zien en direct bewerken.
Geen tabellen, geen data_editor voor snelle edits.
Werkt voor Verbouwing én Inboedel.
"""
import streamlit as st
import pandas as pd
from typing import Callable

from utils.config import KAMER_EMOJIS, CHART_COLORS


# ── Helpers ────────────────────────────────────────────────────────────────

def _sf(v) -> float:
    try:
        return float(str(v or 0).replace(",",".").replace("€","").strip())
    except (TypeError, ValueError):
        return 0.0


def _cat_totaal(df: pd.DataFrame, cat: str) -> float:
    if df.empty or "Categorie" not in df.columns:
        return 0.0
    mask = df["Categorie"] == cat
    return float(df.loc[mask, "Totaal (€)"].apply(_sf).sum()) if mask.any() else 0.0


def _cat_items(df: pd.DataFrame, cat: str) -> list[dict]:
    if df.empty or "Categorie" not in df.columns:
        return []
    rows = df[df["Categorie"] == cat].copy()
    return rows.to_dict(orient="records")


def _replace_cat_items(df: pd.DataFrame, cat: str, items: list[dict]) -> pd.DataFrame:
    """Vervang alle rijen van een categorie met de nieuwe itemlijst."""
    if df.empty:
        return pd.DataFrame(items) if items else pd.DataFrame()
    rest = df[df["Categorie"] != cat].copy()
    if items:
        new_df = pd.DataFrame(items)
        return pd.concat([rest, new_df], ignore_index=True)
    return rest.reset_index(drop=True)


# ── Kleur voor voortgangsbalk ──────────────────────────────────────────────

def _pct_color(pct: float) -> str:
    if pct >= 100:
        return "#EF4444"
    if pct >= 80:
        return "#F59E0B"
    return "#10B981"


# ── Category Card Grid ─────────────────────────────────────────────────────

def render_category_grid(
    df: pd.DataFrame,
    cats: dict[str, float],    # {cat: begroot}
    state_key: str,            # bv. "verb_selected_cat"
    kosten_per_cat: dict[str, float] | None = None,
    cols: int = 3,
) -> None:
    """
    Toon een grid van categorie-kaarten.
    Klik op een kaart → zet state_key → drill-down wordt gerenderd.
    """
    kosten_per_cat = kosten_per_cat or {}
    if not cats:
        st.info("Geen categorieën gevonden. Voeg posten toe via de Bulk Editor.")
        return

    # Kleine "Alle categorieën" info
    totaal_begroot = sum(cats.values())
    totaal_besteed = sum(kosten_per_cat.get(c, 0) for c in cats)
    pct_totaal = totaal_besteed / totaal_begroot * 100 if totaal_begroot > 0 else 0

    st.markdown(f"""
    <div style='background:#fff;border-radius:12px;padding:12px 18px;
                margin-bottom:16px;box-shadow:0 2px 8px rgba(0,0,0,.06);
                display:flex;justify-content:space-between;align-items:center;'>
      <span style='font-weight:700;color:#1A1A2E;font-size:.95rem;'>
        📦 {len(cats)} categorieën &nbsp;·&nbsp;
        💰 € {totaal_begroot:,.0f} totaal begroot
      </span>
      <span style='font-size:.82rem;color:{"#EF4444" if pct_totaal>=100 else "#10B981"};font-weight:600;'>
        {pct_totaal:.0f}% besteed
      </span>
    </div>""", unsafe_allow_html=True)

    grid_cols = st.columns(cols)
    for i, (cat, begroot) in enumerate(sorted(cats.items(), key=lambda x: -x[1])):
        gerealiseerd = kosten_per_cat.get(cat, 0.0)
        pct = min(gerealiseerd / begroot * 100, 100) if begroot > 0 else 0
        emoji = KAMER_EMOJIS.get(cat, "📦")
        kleur = _pct_color(pct)
        rest = begroot - gerealiseerd
        n_items = len(_cat_items(df, cat))

        with grid_cols[i % cols]:
            # Kaart container
            with st.container(border=True):
                st.markdown(f"""
                <div style='padding:4px 0;'>
                  <span style='font-size:1.6rem;'>{emoji}</span>
                  <div style='font-weight:700;font-size:.92rem;color:#1A1A2E;
                               margin:3px 0 2px;line-height:1.2;'>{cat}</div>
                  <div style='font-size:.72rem;color:#6B7280;margin-bottom:6px;'>
                    {n_items} posten · € {begroot:,.0f} begroot
                  </div>
                  <div style='background:#F3F4F6;border-radius:999px;height:6px;
                               margin-bottom:6px;overflow:hidden;'>
                    <div style='width:{pct:.1f}%;height:100%;border-radius:999px;
                                 background:{kleur};'></div>
                  </div>
                  <div style='display:flex;justify-content:space-between;
                               font-size:.76rem;font-weight:600;'>
                    <span style='color:#6B7280;'>{pct:.0f}% gebruikt</span>
                    <span style='color:{"#EF4444" if rest<0 else "#10B981"};'>
                      {"⚠️" if rest<0 else "✓"} € {abs(rest):,.0f} {"over" if rest<0 else "vrij"}
                    </span>
                  </div>
                </div>""", unsafe_allow_html=True)

                if st.button(
                    f"✏️ Bewerken",
                    key=f"edit_cat_{state_key}_{cat}",
                    use_container_width=True,
                    type="primary",
                ):
                    st.session_state[state_key] = cat
                    st.rerun()


# ── Inline Item Editor ─────────────────────────────────────────────────────

def render_item_editor(
    df: pd.DataFrame,
    cat: str,
    state_key: str,
    eenheden: list[str],
    on_save: Callable[[pd.DataFrame], None],
    cat_opties: list[str] | None = None,
    show_eenheid: bool = True,
) -> pd.DataFrame:
    """
    Volledig inline editor voor één categorie.
    Toont huidige items als bewerkbare rijen + quick-add formulier.
    Retourneert de bijgewerkte DataFrame na elke actie.

    on_save: callback(df) die de DataFrame opslaat naar session_state + Excel.
    """
    items = _cat_items(df, cat)
    emoji = KAMER_EMOJIS.get(cat, "📦")

    # ── Header met terugknop ──────────────────────────────────────────
    c_back, c_title = st.columns([1, 6])
    with c_back:
        if st.button("← Terug", key=f"back_{state_key}", use_container_width=True):
            st.session_state[state_key] = None
            st.rerun()
    with c_title:
        totaal_cat = sum(_sf(i.get("Totaal (€)", 0)) for i in items)
        st.markdown(f"""
        <div style='padding:8px 0;'>
          <span style='font-size:1.5rem;'>{emoji}</span>
          <strong style='font-size:1.1rem;color:#1A1A2E;margin-left:8px;'>{cat}</strong>
          <span style='margin-left:12px;font-size:.85rem;color:#6B7280;'>
            {len(items)} posten · <strong style='color:#1A1A2E;'>€ {totaal_cat:,.2f}</strong> totaal
          </span>
        </div>""", unsafe_allow_html=True)

    st.markdown("---")

    # ── Bestaande items — inline bewerkbaar ─────────────────────────
    changed = False
    items_updated = list(items)

    if items:
        # Kolom headers
        hc = st.columns([4, 2, 1, 0.6] if show_eenheid else [5, 2, 0.6])
        hc[0].markdown("<span style='font-size:.72rem;color:#6B7280;font-weight:700;text-transform:uppercase;letter-spacing:.06em;'>OMSCHRIJVING</span>", unsafe_allow_html=True)
        hc[1].markdown("<span style='font-size:.72rem;color:#6B7280;font-weight:700;text-transform:uppercase;letter-spacing:.06em;'>BEDRAG (€)</span>", unsafe_allow_html=True)
        if show_eenheid:
            hc[2].markdown("<span style='font-size:.72rem;color:#6B7280;font-weight:700;text-transform:uppercase;letter-spacing:.06em;'>EENHEID</span>", unsafe_allow_html=True)

        for idx, item in enumerate(items_updated):
            if show_eenheid:
                c1, c2, c3, c4 = st.columns([4, 2, 1, 0.6])
            else:
                c1, c2, c4 = st.columns([5, 2, 0.6])

            with c1:
                new_post = st.text_input(
                    "Post", value=str(item.get("Post", "")),
                    key=f"post_{state_key}_{cat}_{idx}",
                    label_visibility="collapsed",
                    placeholder="Omschrijving...",
                )
            with c2:
                cur_bedrag = _sf(item.get("Totaal (€)", item.get("Bedrag (€)", 0)))
                new_bedrag = st.number_input(
                    "Bedrag", value=cur_bedrag,
                    min_value=0.0, step=50.0, format="%.2f",
                    key=f"bedrag_{state_key}_{cat}_{idx}",
                    label_visibility="collapsed",
                )
            if show_eenheid:
                with c3:
                    cur_eenh = str(item.get("Eenheid", "stuks"))
                    new_eenh = st.selectbox(
                        "Eenh", options=eenheden,
                        index=eenheden.index(cur_eenh) if cur_eenh in eenheden else 0,
                        key=f"eenh_{state_key}_{cat}_{idx}",
                        label_visibility="collapsed",
                    )
            with c4:
                if st.button("🗑️", key=f"del_{state_key}_{cat}_{idx}",
                             help="Verwijder deze post"):
                    items_updated.pop(idx)
                    new_df = _replace_cat_items(df, cat, items_updated)
                    on_save(new_df)
                    st.rerun()

            # Detecteer wijzigingen
            if show_eenheid:
                if (new_post != str(item.get("Post","")) or
                    abs(new_bedrag - _sf(item.get("Totaal (€)", 0))) > 0.001 or
                    new_eenh != str(item.get("Eenheid","stuks"))):
                    items_updated[idx] = {
                        **item,
                        "Post":       new_post,
                        "Totaal (€)": new_bedrag,
                        "Eenheid":    new_eenh,
                        "Categorie":  cat,
                    }
                    changed = True
            else:
                if (new_post != str(item.get("Post","")) or
                    abs(new_bedrag - _sf(item.get("Totaal (€)", 0))) > 0.001):
                    items_updated[idx] = {
                        **item,
                        "Post":       new_post,
                        "Totaal (€)": new_bedrag,
                        "Categorie":  cat,
                    }
                    changed = True

        # Opslaan knop — alleen zichtbaar als er iets gewijzigd is
        if changed:
            st.markdown("<div style='height:4px'></div>", unsafe_allow_html=True)
            if st.button("💾 Wijzigingen opslaan", type="primary",
                         use_container_width=True,
                         key=f"save_items_{state_key}_{cat}"):
                new_df = _replace_cat_items(df, cat, items_updated)
                on_save(new_df)
                st.success("✅ Opgeslagen!")
                st.rerun()

    else:
        st.info(f"Nog geen posten in '{cat}'. Voeg hieronder je eerste post toe.")

    st.markdown("---")

    # ── QUICK-ADD FORMULIER ──────────────────────────────────────────
    st.markdown(f"#### ➕ Snel toevoegen aan **{cat}**")

    with st.form(f"quickadd_{state_key}_{cat}", clear_on_submit=True):
        if show_eenheid:
            qa1, qa2, qa3 = st.columns([4, 2, 1])
        else:
            qa1, qa2 = st.columns([4, 2])

        with qa1:
            qa_naam = st.text_input(
                "Omschrijving",
                placeholder="bijv. KitchenAid mixer",
            )
        with qa2:
            qa_bedrag = st.number_input(
                "Bedrag (€)",
                min_value=0.0, step=50.0, format="%.2f",
            )
        if show_eenheid:
            with qa3:
                qa_eenh = st.selectbox("Eenheid", eenheden)

        qa_opmerking = st.text_input(
            "Opmerking (optioneel)",
            placeholder="bijv. 'besteld bij Bol.com'",
        )

        submitted = st.form_submit_button(
            f"➕ Toevoegen aan {cat}",
            type="primary",
            use_container_width=True,
        )
        if submitted:
            if not qa_naam.strip():
                st.error("Voer een omschrijving in.")
            elif qa_bedrag <= 0:
                st.error("Voer een bedrag groter dan € 0 in.")
            else:
                new_item = {
                    "Categorie":              cat,
                    "Post":                   qa_naam.strip(),
                    "Aantal":                 1.0,
                    "Eenheid":                qa_eenh if show_eenheid else "stuks",
                    "Kosten per eenheid (€)": qa_bedrag,
                    "Totaal (€)":             qa_bedrag,
                    "Opmerking":              qa_opmerking,
                }
                items_new = items_updated + [new_item]
                new_df = _replace_cat_items(df, cat, items_new)
                on_save(new_df)
                st.success(f"✅ '{qa_naam}' (€ {qa_bedrag:,.2f}) toegevoegd!")
                st.rerun()

    # Totaalregel
    totaal_huidig = sum(_sf(i.get("Totaal (€)", 0)) for i in items_updated)
    st.markdown(f"""
    <div style='background:#F9FAFB;border-radius:10px;padding:12px 16px;
                margin-top:8px;display:flex;justify-content:space-between;align-items:center;'>
      <span style='font-size:.82rem;color:#6B7280;'>{len(items_updated)} posten</span>
      <span style='font-size:1rem;font-weight:800;color:#1A1A2E;'>
        Totaal: € {totaal_huidig:,.2f}
      </span>
    </div>""", unsafe_allow_html=True)

    return _replace_cat_items(df, cat, items_updated)


# ── Budget-aanpassing per categorie ───────────────────────────────────────

def render_budget_adjuster(
    cat: str,
    begroot: float,
    state_key: str,
    on_budget_save: Callable[[str, float], None],
) -> None:
    """
    Compact budget-aanpas widget voor één categorie.
    """
    st.markdown("##### 💰 Budget aanpassen")
    cols = st.columns([3, 1])
    with cols[0]:
        new_budget = st.number_input(
            f"Begroot budget voor {cat} (€)",
            value=begroot, min_value=0.0, step=500.0, format="%.2f",
            key=f"budget_adj_{state_key}_{cat}",
        )
    with cols[1]:
        st.markdown("<div style='height:28px'></div>", unsafe_allow_html=True)
        if st.button("💾", key=f"save_budget_adj_{state_key}_{cat}",
                     help="Budget opslaan", use_container_width=True):
            on_budget_save(cat, new_budget)
            st.success(f"✅ Budget bijgewerkt naar € {new_budget:,.2f}")
            st.rerun()
