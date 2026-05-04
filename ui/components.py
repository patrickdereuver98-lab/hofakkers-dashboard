"""
ui/components.py
Herbruikbare UI componenten.
"""
import streamlit as st
from config.config import COLORS

def render_card(title, content, emoji=""):
    """Rendert een gestylde card."""
    st.markdown(f"""
    <div style="background: linear-gradient(135deg, {COLORS['primary']}, {COLORS['secondary']});
                border-radius: 15px; padding: 20px; margin: 10px 0; color: white; box-shadow: 0 4px 6px rgba(0,0,0,0.1);">
        <h3>{emoji} {title}</h3>
        {content}
    </div>
    """, unsafe_allow_html=True)

def render_metric(title, value, delta=None):
    """Rendert een metric."""
    delta_html = f"<div style='color: green; font-size: 0.8em;'>{delta}</div>" if delta else ""
    st.markdown(f"""
    <div style="text-align: center; margin: 10px 0;">
        <h4>{title}</h4>
        <h2>{value}</h2>
        {delta_html}
    </div>
    """, unsafe_allow_html=True)

def render_progress_bar(value, max_value, label=""):
    """Rendert een progress bar."""
    percentage = min((value / max_value) * 100, 100) if max_value > 0 else 0
    st.markdown(f"""
    <div style="margin: 10px 0;">
        <div style="display: flex; justify-content: space-between;">
            <span>{label}</span>
            <span>{percentage:.1f}%</span>
        </div>
        <div style="width: 100%; background-color: #e0e0e0; border-radius: 10px; height: 20px;">
            <div style="width: {percentage}%; height: 100%; background-color: {COLORS['primary']}; border-radius: 10px;"></div>
        </div>
    </div>
    """, unsafe_allow_html=True)

def render_task_card(task, status):
    """Rendert een taak card."""
    color = {"Todo": "#FFA500", "Bezig": "#FFD700", "Gereed": "#32CD32"}.get(status, "#FFD700")
    st.markdown(f"""
    <div style="background-color: {color}; border-radius: 10px; padding: 10px; margin: 5px 0; color: black;">
        <strong>{task}</strong> - {status}
    </div>
    """, unsafe_allow_html=True)