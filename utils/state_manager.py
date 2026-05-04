"""
utils/state_manager.py
State management voor st.session_state.
"""
import streamlit as st
import pandas as pd
from utils.excel_handler import load_all_data, save_all_data
from utils.config import DEFAULT_ROOMS, TASK_STATUSES, WISH_STATUSES


def init_session_state():
    if 'data_loaded' not in st.session_state:
        data = load_all_data()
        st.session_state.update(data)
        st.session_state['data_loaded'] = True
        _normalize_state()


def _normalize_state():
    st.session_state.setdefault('dashboard', {})
    st.session_state.setdefault('verbouwing', pd.DataFrame())
    st.session_state.setdefault('budget_verdeling', pd.DataFrame())
    st.session_state.setdefault('tasks', {})
    st.session_state.setdefault('wishes', {})
    st.session_state.setdefault('kosten', {})
    st.session_state.setdefault('bonnen', [])
    st.session_state.setdefault('rooms', DEFAULT_ROOMS)
    st.session_state.setdefault('users', [])

    st.session_state['rooms'] = sorted(set(st.session_state['rooms']) | set(st.session_state['verbouwing'].get('Kamer', []).dropna().unique()))

    for room in st.session_state['rooms']:
        st.session_state['tasks'].setdefault(room, [])
        st.session_state['wishes'].setdefault(room, [])
        st.session_state['kosten'].setdefault(room, [])

    if 'budget_verdeling' in st.session_state and not st.session_state['budget_verdeling'].empty:
        rooms_in_budget = st.session_state['budget_verdeling']['Kamer'].fillna('Algemeen').tolist()
        missing = [room for room in st.session_state['rooms'] if room not in rooms_in_budget]
        if missing:
            extra = pd.DataFrame({
                'Kamer': missing,
                'Toegewezen Budget (€)': [0.0] * len(missing),
                'Gerealiseerd (€)': [0.0] * len(missing),
                'Beschikbaar (€)': [0.0] * len(missing),
            })
            st.session_state['budget_verdeling'] = pd.concat([st.session_state['budget_verdeling'], extra], ignore_index=True)
    else:
        st.session_state['budget_verdeling'] = pd.DataFrame({
            'Kamer': st.session_state['rooms'],
            'Toegewezen Budget (€)': [0.0] * len(st.session_state['rooms']),
            'Gerealiseerd (€)': [0.0] * len(st.session_state['rooms']),
            'Beschikbaar (€)': [0.0] * len(st.session_state['rooms']),
        })


def get_rooms():
    return st.session_state.get('rooms', DEFAULT_ROOMS)


def get_dashboard():
    return st.session_state.get('dashboard', {})


def get_dashboard_dataframe():
    dashboard = get_dashboard()
    return pd.DataFrame(list(dashboard.items()), columns=['Sleutel', 'Waarde'])


def save_dashboard_dataframe(df):
    dashboard = {}
    for _, row in df.iterrows():
        key = str(row.get('Sleutel', '')).strip()
        if key:
            dashboard[key] = row.get('Waarde', 0)
    st.session_state['dashboard'] = dashboard


def get_budget_data():
    return st.session_state.get('budget_verdeling', pd.DataFrame())


def save_budget_data(df):
    st.session_state['budget_verdeling'] = df.copy()


def get_tasks(room):
    return st.session_state.get('tasks', {}).get(room, [])


def save_tasks(room, tasks):
    st.session_state['tasks'][room] = tasks


def get_wishes(room):
    return st.session_state.get('wishes', {}).get(room, [])


def save_wishes(room, wishes):
    st.session_state['wishes'][room] = wishes


def get_costs(room):
    return st.session_state.get('kosten', {}).get(room, [])


def save_costs(room, costs):
    st.session_state['kosten'][room] = costs


def get_room_verbouwing(room):
    verbouwing = st.session_state.get('verbouwing', pd.DataFrame())
    if verbouwing.empty or 'Kamer' not in verbouwing.columns:
        return pd.DataFrame(columns=verbouwing.columns)
    return verbouwing[verbouwing['Kamer'] == room].copy()


def update_verbouwing(room, df):
    verbouwing = st.session_state.get('verbouwing', pd.DataFrame())
    remaining = verbouwing[verbouwing['Kamer'] != room]
    st.session_state['verbouwing'] = pd.concat([remaining, df], ignore_index=True)


def save_session_state_to_excel():
    return save_all_data({
        'dashboard': st.session_state.get('dashboard', {}),
        'verbouwing': st.session_state.get('verbouwing', pd.DataFrame()),
        'budget_verdeling': st.session_state.get('budget_verdeling', pd.DataFrame()),
        'tasks': st.session_state.get('tasks', {}),
        'wishes': st.session_state.get('wishes', {}),
        'kosten': st.session_state.get('kosten', {}),
        'bonnen': st.session_state.get('bonnen', []),
    })
