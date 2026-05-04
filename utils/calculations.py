"""
utils/calculations.py
Foutloze reken-engine voor het Hofakkers 44 dashboard.
"""
import streamlit as st
import pandas as pd
from utils.state_manager import get_budget_data, get_tasks, get_wishes, get_costs, get_room_verbouwing, get_dashboard


def calculate_totals():
    dashboard = get_dashboard()
    totaal_budget = float(dashboard.get('Totaal Inleg Patrick', 0) or 0) + float(dashboard.get('Totaal Inleg Willianne', 0) or 0)
    verbouwing = st.session_state.get('verbouwing', pd.DataFrame())
    verbouwing_sum = float(verbouwing['Totaal (€)'].sum()) if not verbouwing.empty and 'Totaal (€)' in verbouwing.columns else 0.0
    kosten_sum = 0.0
    for costs in st.session_state.get('kosten', {}).values():
        for cost in costs:
            kosten_sum += float(cost.get('Bedrag (€)', 0) or 0)
    besteed = verbouwing_sum + kosten_sum
    beschikbaar = totaal_budget - besteed
    return {
        'totaal_budget': totaal_budget,
        'besteed': besteed,
        'beschikbaar': beschikbaar,
        'percentage': round((besteed / totaal_budget * 100), 2) if totaal_budget > 0 else 0.0,
    }


def calculate_room_summary(room):
    budget_data = get_budget_data()
    budget_row = budget_data[budget_data['Kamer'] == room]
    assigned = float(budget_row['Toegewezen Budget (€)'].sum()) if not budget_row.empty else 0.0
    verbouwing = get_room_verbouwing(room)
    verbouwing_spent = float(verbouwing['Totaal (€)'].sum()) if not verbouwing.empty and 'Totaal (€)' in verbouwing.columns else 0.0
    costs = get_costs(room)
    extra_spent = sum(float(cost.get('Bedrag (€)', 0) or 0) for cost in costs)
    total_spent = verbouwing_spent + extra_spent
    remaining = assigned - total_spent
    tasks = get_tasks(room)
    completed = len([task for task in tasks if task.get('Status') == 'Gereed'])
    total_tasks = len(tasks)
    progress = round((completed / total_tasks * 100), 1) if total_tasks > 0 else 0.0
    wishes = get_wishes(room)
    return {
        'room': room,
        'budget': assigned,
        'spent': total_spent,
        'remaining': remaining,
        'task_count': total_tasks,
        'completed_tasks': completed,
        'progress': progress,
        'wish_count': len(wishes),
        'verbouwing_spent': verbouwing_spent,
        'costs_spent': extra_spent,
    }


def calculate_budget_distribution():
    budget_data = get_budget_data()
    result = []
    for _, row in budget_data.iterrows():
        result.append({
            'kamer': row['Kamer'],
            'budget': float(row['Toegewezen Budget (€)'] or 0),
            'spent': float(row['Gerealiseerd (€)'] or 0),
            'remaining': float(row['Beschikbaar (€)'] or 0),
        })
    return result


def calculate_user_shares():
    dashboard = get_dashboard()
    total = float(dashboard.get('Totaal Inleg Patrick', 0) or 0) + float(dashboard.get('Totaal Inleg Willianne', 0) or 0)
    patrick = float(dashboard.get('Totaal Inleg Patrick', 0) or 0)
    willianne = float(dashboard.get('Totaal Inleg Willianne', 0) or 0)
    return {
        'Patrick': {'value': patrick, 'percentage': round((patrick / total * 100), 1) if total > 0 else 0.0},
        'Willianne': {'value': willianne, 'percentage': round((willianne / total * 100), 1) if total > 0 else 0.0},
        'total': total,
    }


def calculate_overall_progress():
    rooms = sorted(st.session_state.get('rooms', []))
    if not rooms:
        return 0.0
    total = 0.0
    count = 0
    for room in rooms:
        summary = calculate_room_summary(room)
        total += summary['progress']
        count += 1
    return round(total / count, 1) if count > 0 else 0.0
