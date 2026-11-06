"""
Agent 6 — Early Warning & Alert Agent detail page.
"""
import streamlit as st
import plotly.graph_objects as go
from datetime import datetime
from pages.agents._agent_base import (
    page_header, how_it_works_panel, result_report_card, run_agent_button
)

ALERTS = [
    {
        "level": "RED",    "color": "#E53935", "bg": "#1A0505",
        "district": "Visakhapatnam",
        "message": "Extremely Severe Cyclonic Storm VARUNA expected to make landfall within 48 hours. Maximum sustained winds 130 kt. Life-threatening storm surge 3–5m. Complete evacuation of coastal areas within 10 km mandatory.",
        "action": "Evacuate immediately · Shelter activation · Port closure · NDRF deployment",
        "issued": "02:00 IST",
    },
    {
        "level": "RED",    "color": "#E53935", "bg": "#1A0505",
        "district": "Srikakulam",
        "message": "Severe cyclonic conditions. Storm surge 2–4m expected. Fishing vessels must return to port immediately. Low-lying areas must evacuate.",
        "action": "Evacuate coastal belt · Close schools · Pre-position relief materials",
        "issued": "02:00 IST",
    },
    {
        "level": "ORANGE", "color": "#FF6D00", "bg": "#1A0D00",
        "district": "East Godavari",
        "message": "Cyclone VARUNA peripheral winds and heavy rainfall expected. Flash floods possible in low-lying areas.",
        "action": "High alert · Monitor regularly · Shelter in place if unable to evacuate",
        "issued": "02:15 IST",
    },
    {
        "level": "ORANGE", "color": "#FF6D00", "bg": "#1A0D00",
        "district": "Ganjam (Odisha)",
        "message": "Strong cyclonic winds (60–80 kt) and heavy rainfall in next 36 hours.",
        "action": "Activate district control rooms · Pre-position ODRAF teams",
        "issued": "02:15 IST",
    },
    {
        "level": "YELLOW", "color": "#FFD600", "bg": "#1A1400",
        "district": "Puri (Odisha)",
        "message": "Heavy rainfall and strong winds expected. No immediate threat to life but property at risk.",
        "action": "Remain alert · Avoid coastal areas · Monitor official bulletins",
        "issued": "02:30 IST",
    },
]


def _alert_card(alert: dict):
    st.markdown(
        f'<div style="background:{alert["bg"]};border:1px solid {alert["color"]};'
        f'border-left:5px solid {alert["color"]};border-radius:10px;'
        f'padding:14px 18px;margin-bottom:10px">'
        f'<div style="display:flex;justify-content:space-between;align-items:center">'
        f'<span style="color:{alert["color"]};font-weight:800;font-size:1rem">'
        f'🚨 {alert["level"]} ALERT</span>'
        f'<span style="color:#8B949E;font-size:0.78rem">Issued: {alert["issued"]}</span>'
        f'</div>'
        f'<div style="color:#E6EDF3;font-weight:600;font-size:0.92rem;margin:6px 0 4px">'
        f'📍 {alert["district"]}</div>'
        f'<div style="color:#C9D1D9;font-size:0.82rem;margin-bottom:8px">'
        f'{alert["message"]}</div>'
        f'<div style="background:rgba(255,255,255,0.04);border-radius:6px;'
        f'padding:6px 10px;font-size:0.78rem;color:{alert["color"]}">'
        f'<strong>Recommended Action:</strong> {alert["action"]}'
        f'</div>'
        f'</div>',
        unsafe_allow_html=True,
    )


def render():
    page_header(
        agent_name="Early Warning & Alert Agent",
        icon="🚨",
        tagline="Generates location-specific alerts and preparedness recommendations for communities and authorities.",
        llm="llama3-70b-8192",
        provider="groq",
    )
    how_it_works_panel(
        llm="Groq Cloud · LLaMA 3-70B",
        tools=["generate_alert", "get_district_contacts", "broadcast_sms_alert"],
        memory="Short-term session buffer + ChromaDB RAG",
        guardrails="Input, Output, Operational, HITL, Ethical",
        react_steps=3,
        token_budget=2048,
    )

    st.divider()

    # Alert summary KPIs
    st.markdown("### 🚨 Active Alerts Summary")
    k1, k2, k3, k4, k5 = st.columns(5)
    for col, lbl, val, c in [
        (k1, "RED Alerts",       "2", "#E53935"),
        (k2, "ORANGE Alerts",    "2", "#FF6D00"),
        (k3, "YELLOW Alerts",    "1", "#FFD600"),
        (k4, "Districts Alerted","5", "#4FC3F7"),
        (k5, "SMS Bulletins",    "3", "#69F0AE"),
    ]:
        with col:
            st.markdown(
                f'<div style="background:#161B22;border:1px solid #30363D;border-radius:8px;'
                f'padding:12px;text-align:center">'
                f'<div style="font-weight:700;color:{c};font-size:1.5rem">{val}</div>'
                f'<div style="font-size:0.7rem;color:#8B949E;text-transform:uppercase">{lbl}</div>'
                f'</div>',
                unsafe_allow_html=True,
            )

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("### 📋 Active Alerts")

    filter_col, _ = st.columns([1, 3])
    with filter_col:
        level_filter = st.selectbox("Filter by alert level",
                                    ["All", "RED", "ORANGE", "YELLOW"], index=0)

    for alert in ALERTS:
        if level_filter == "All" or alert["level"] == level_filter:
            _alert_card(alert)

    st.divider()
    st.markdown("### 📡 Alert Dissemination Channels")
    channels_html = '<div style="display:flex;flex-wrap:wrap;gap:8px;margin-bottom:12px">'
    channels = [
        ("📱 SMS Broadcast",   "#4FC3F7", "3.2M recipients"),
        ("📻 All India Radio", "#81C784", "Active"),
        ("📺 DD National",     "#FFD600", "Emergency broadcast"),
        ("🔔 Common Alert Protocol", "#CE93D8", "NDMA relay"),
        ("🌐 IMD Portal",      "#FF6D00", "Public bulletin"),
        ("🚁 NDRF Control",    "#E53935", "Ops center"),
    ]
    for name, color, sub in channels:
        channels_html += (
            f'<div style="background:#161B22;border:1px solid #30363D;border-radius:8px;'
            f'padding:10px 14px;border-left:3px solid {color}">'
            f'<div style="font-size:0.85rem;color:#E6EDF3;font-weight:600">{name}</div>'
            f'<div style="font-size:0.72rem;color:{color}">{sub}</div>'
            f'</div>'
        )
    channels_html += '</div>'
    st.markdown(channels_html, unsafe_allow_html=True)

    st.divider()
    st.markdown("### 🤖 Agent Output")
    results = st.session_state.get("agent_results", {})
    result_report_card(results.get("warning", {}))
    run_agent_button("warning", "▶ Run Early Warning Agent")
