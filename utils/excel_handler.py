"""
utils/excel_handler.py
Robuuste Excel I/O en mapping naar de app-state.
"""
import streamlit as st
import pandas as pd
import openpyxl
from openpyxl.utils.dataframe import dataframe_to_rows
from pathlib import Path
from utils.config import (
    EXCEL_FILE,
    DEFAULT_ROOMS,
    DEFAULT_TASK_STATUSES,
    DEFAULT_WISH_STATUSES,
    BUDGET_CATEGORIES,
)

EXPECTED_VERBOUWING_COLUMNS = [
    'Categorie', 'Post', 'Aantal', 'Eenheid', 'Kosten per eenheid (€)',
    'Totaal (€)', 'Opmerking', 'Kamer'
]

def file_exists():
    return EXCEL_FILE.exists()

def _safe_read_excel():
    try:
        sheets = pd.read_excel(EXCEL_FILE, sheet_name=None, engine='openpyxl')
        return sheets
    except Exception as exc:
        raise RuntimeError(f"Kon Excel niet lezen: {exc}") from exc

def _normalize_dataframe(df, expected_columns):
    if df is None:
        return pd.DataFrame(columns=expected_columns)
    df = df.copy()
    df.columns = [str(col).strip() for col in df.columns]
    for column in expected_columns:
        if column not in df.columns:
            df[column] = "" if column != 'Aantal' and column != 'Kosten per eenheid (€)' and column != 'Totaal (€)' else 0
    df = df[expected_columns].copy()
    return df

def _load_dashboard(sheet_df):
    if sheet_df is None:
        return {}
    sheet_df = sheet_df.copy()
    sheet_df.columns = [str(col).strip() for col in sheet_df.columns]
    if sheet_df.shape[1] < 2:
        return {}
    key = sheet_df.columns[0]
    value = sheet_df.columns[1]
    data = {}
    for _, row in sheet_df.iterrows():
        if pd.isna(row[key]):
            continue
        data[str(row[key]).strip()] = row[value] if not pd.isna(row[value]) else 0
    return data

def _load_verbouwing(sheet_df):
    df = _normalize_dataframe(sheet_df, EXPECTED_VERBOUWING_COLUMNS)
    df = df.dropna(subset=['Post'], how='all')
    if 'Kamer' not in df or df['Kamer'].isna().all():
        df['Kamer'] = 'Algemeen'
    df['Kamer'] = df['Kamer'].fillna('Algemeen')
    df['Aantal'] = pd.to_numeric(df['Aantal'], errors='coerce').fillna(0)
    df['Kosten per eenheid (€)'] = pd.to_numeric(df['Kosten per eenheid (€)'], errors='coerce').fillna(0)
    df['Totaal (€)'] = pd.to_numeric(df['Totaal (€)'], errors='coerce').fillna(df['Aantal'] * df['Kosten per eenheid (€)'])
    return df

def _load_list_by_room(sheet_df, room_key, expected_columns):
    df = _normalize_dataframe(sheet_df, expected_columns)
    df[room_key] = df[room_key].fillna('Algemeen')
    result = {}
    for _, row in df.iterrows():
        room = str(row[room_key]).strip() if not pd.isna(row[room_key]) else 'Algemeen'
        item = {col: row[col] for col in expected_columns if col != room_key}
        item['Kamer'] = room
        result.setdefault(room, []).append(item)
    return result

def _load_tasks(sheet_df):
    columns = ['Kamer', 'Taak', 'Status', 'Opmerking']
    if sheet_df is None:
        return {}
    return _load_list_by_room(sheet_df, 'Kamer', columns)

def _load_wishes(sheet_df):
    columns = ['Kamer', 'Wens', 'Status', 'Opmerking']
    if sheet_df is None:
        return {}
    return _load_list_by_room(sheet_df, 'Kamer', columns)

def _load_costs(sheet_df):
    columns = ['Kamer', 'Datum', 'Leverancier', 'Bedrag (€)', 'Categorie', 'Omschrijving']
    if sheet_df is None:
        return {}
    df = sheet_df.copy()
    df.columns = [str(col).strip() for col in df.columns]
    if 'Bedrag (€)' not in df.columns and 'Bedrag' in df.columns:
        df['Bedrag (€)'] = df['Bedrag']
    result = _load_list_by_room(df, 'Kamer', columns)
    return result

def _load_bonnen(sheet_df):
    if sheet_df is None:
        return []
    df = sheet_df.copy()
    df.columns = [str(col).strip() for col in df.columns]
    return df.to_dict(orient='records')

def _load_budget(sheet_df, rooms):
    columns = ['Kamer', 'Toegewezen Budget (€)', 'Gerealiseerd (€)', 'Beschikbaar (€)']
    if sheet_df is None or sheet_df.empty:
        data = {
            'Kamer': rooms,
            'Toegewezen Budget (€)': [0.0] * len(rooms),
            'Gerealiseerd (€)': [0.0] * len(rooms),
            'Beschikbaar (€)': [0.0] * len(rooms),
        }
        return pd.DataFrame(data)
    budget_df = sheet_df.copy()
    budget_df.columns = [str(col).strip() for col in budget_df.columns]
    for column in columns:
        if column not in budget_df.columns:
            budget_df[column] = 0.0
    budget_df = budget_df[columns].copy()
    budget_df['Kamer'] = budget_df['Kamer'].fillna('Algemeen')
    budget_df['Toegewezen Budget (€)'] = pd.to_numeric(budget_df['Toegewezen Budget (€)'], errors='coerce').fillna(0)
    budget_df['Gerealiseerd (€)'] = pd.to_numeric(budget_df['Gerealiseerd (€)'], errors='coerce').fillna(0)
    budget_df['Beschikbaar (€)'] = pd.to_numeric(budget_df['Beschikbaar (€)'], errors='coerce').fillna(0)
    missing_rooms = [room for room in rooms if room not in budget_df['Kamer'].tolist()]
    if missing_rooms:
        extra = pd.DataFrame({
            'Kamer': missing_rooms,
            'Toegewezen Budget (€)': 0.0,
            'Gerealiseerd (€)': 0.0,
            'Beschikbaar (€)': 0.0,
        })
        budget_df = pd.concat([budget_df, extra], ignore_index=True)
    return budget_df

def load_all_data():
    if not file_exists():
        raise FileNotFoundError(f"Excel bestand niet gevonden op {EXCEL_FILE}")

    sheets = _safe_read_excel()
    dashboard = _load_dashboard(sheets.get('Dashboard PRO'))
    verbouwing = _load_verbouwing(sheets.get('Verbouwing begroting'))
    rooms = sorted({room for room in verbouwing['Kamer'].dropna().unique()} | set(DEFAULT_ROOMS))
    budget_verdeling = _load_budget(sheets.get('Budget Verdeling'), rooms)
    tasks = _load_tasks(sheets.get('Taken'))
    wishes = _load_wishes(sheets.get('Wensen'))
    costs = _load_costs(sheets.get('Kosten'))
    bonnen = _load_bonnen(sheets.get('Bonnen'))

    return {
        'dashboard': dashboard,
        'verbouwing': verbouwing,
        'budget_verdeling': budget_verdeling,
        'tasks': tasks,
        'wishes': wishes,
        'kosten': costs,
        'bonnen': bonnen,
        'rooms': rooms,
        'users': [key for key in dashboard.keys() if 'Inleg' in key or key in ['Patrick', 'Willianne']]
    }

def _write_dataframe_to_sheet(wb, sheet_name, df):
    if sheet_name in wb.sheetnames:
        ws = wb[sheet_name]
        wb.remove(ws)
    ws = wb.create_sheet(sheet_name)
    for row in dataframe_to_rows(df, index=False, header=True):
        ws.append(row)


def _dict_list_to_dataframe(dict_list, columns):
    if not dict_list:
        return pd.DataFrame(columns=columns)
    return pd.DataFrame(dict_list, columns=columns)

def _save_row_dicts_to_sheet(wb, sheet_name, dict_obj, columns):
    rows = []
    for room, items in dict_obj.items():
        for item in items:
            row = {key: item.get(key, '') for key in columns if key != 'Kamer'}
            row['Kamer'] = room
            rows.append(row)
    df = pd.DataFrame(rows, columns=columns)
    _write_dataframe_to_sheet(wb, sheet_name, df)

def save_all_data(state):
    try:
        wb = openpyxl.load_workbook(EXCEL_FILE)

        dashboard = state.get('dashboard', {})
        dashboard_df = pd.DataFrame(list(dashboard.items()), columns=['Key', 'Value'])
        _write_dataframe_to_sheet(wb, 'Dashboard PRO', dashboard_df)

        verbouwing = state.get('verbouwing', pd.DataFrame())
        _write_dataframe_to_sheet(wb, 'Verbouwing begroting', verbouwing)

        budget_verdeling = state.get('budget_verdeling', pd.DataFrame())
        _write_dataframe_to_sheet(wb, 'Budget Verdeling', budget_verdeling)

        _save_row_dicts_to_sheet(wb, 'Taken', state.get('tasks', {}), ['Kamer', 'Taak', 'Status', 'Opmerking'])
        _save_row_dicts_to_sheet(wb, 'Wensen', state.get('wishes', {}), ['Kamer', 'Wens', 'Status', 'Opmerking'])
        _save_row_dicts_to_sheet(wb, 'Kosten', state.get('kosten', {}), ['Kamer', 'Datum', 'Leverancier', 'Bedrag (€)', 'Categorie', 'Omschrijving'])

        bonnen = state.get('bonnen', [])
        bonnen_df = pd.DataFrame(bonnen, columns=['Datum', 'Leverancier', 'Bedrag (€)', 'Categorie', 'Kamer', 'Omschrijving'])
        _write_dataframe_to_sheet(wb, 'Bonnen', bonnen_df)

        wb.save(EXCEL_FILE)
        return True
    except Exception as exc:
        st.error(f"Kon Excel niet schrijven: {exc}")
        return False

