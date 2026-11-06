"""
Agent 7 — Disaster Response Recommendation Agent detail page.
"""
import streamlit as st
import plotly.graph_objects as go
import pandas as pd
from pages.agents._agent_base import (
    page_header, how_it_works_panel, result_report_card, run_agent_button
)

RESPONSE_PLAN = [
    {
        "category": "Evacuation",
        "icon": "🚌",
        "color": "#E53935",
        "priority": "CRITICAL",
        "actions": [
            "Evacuate 847 coastal villages within 10 km of shore — Visakhapatnam & Srikakulam",
            "Deploy 120 APSRTC buses for mass evacuation — start T-36h",
            "Activate 312 cyclone shelters with 4.2M capacity",
            "Special arrangements for 48,000 differently-abled persons",
        ],
    },
    {
        "category": "Emergency Resources",
        "icon": "🏥",
        "color": "#FF6D00",
        "priority": "HIGH",
        "actions": [
            "Pre-position 14 NDRF battalions across 5 coastal districts",
            "Mobile medical units (42) at shelter entry points",
            "6,200 MT food grain + 18,000 water pouches pre-positioned",
            "Activate emergency power backup for all critical infrastructure",
        ],
    },
    {
        "category": "Infrastructure Protection",
        "icon": "🏗️",
        "color": "#FFD600",
        "priority": "HIGH",
        "actions": [
            "Emergency closure of Visakhapatnam and Kakinada ports",
            "Suspend fishing operations — all vessels must berth",
            "Reinforce embankments at 23 identified breach-prone sites",
            "Backup power to 890 km of transmission lines",
        ],
    },
    {
        "category": "Communication & Coordination",
        "icon": "📡",
        "color": "#4FC3F7",
        "priority": "MEDIUM",
        "actions": [
            "Activate State Emergency Operations Center 24/7",
            "Satellite phones deployed to all district collectors",
            "Ham radio network activated for last-mile communication",
            "Real-time status updates every 3 hours via SDMA portal",
        ],
    },
    {
        "category": "Post-Landfall Recovery",
        "icon": "🔧",
        "color": "#81C784",
        "priority": "PLAN",
        "actions": [
            "Rapid damage assessment teams pre-identified (156 teams)",
            "Emergency repair crews for power restoration staged",
            "Crop damage assessment protocol activated (T+72h)",
            "Psychosocial support teams deployed to major shelters",
        ],
    },
]


def _response_card(item: dict):
    p_color = {
        "CRITICAL": "#E53935", "HIGH": "#FF6D00",
        "MEDIUM": "#FFD600", "PLAN": "#4FC3F7",
    }.get(item["priority"], "#8B949E")
    actions_html = "".join(
        f'<li style="margin-bottom:4px;color:#C9D1D9">{a}</li>'
        for a in item["actions"]
    )
    st.markdown(
        f'<div style="background:#161B22;border:1px solid #30363D;'
        f'border-left:4px solid {item["color"]};border-radius:10px;'
        f'padding:14px 18px;margin-bottom:10px">'
        f'<div style="display:flex;align-items:center;gap:10px;margin-bottom:8px">'
        f'<span style="font-size:1.3rem">{item["icon"]}</span>'
        f'<strong style="color:#E6EDF3;font-size:0.95rem">{item["category"]}</strong>'
        f'<span style="background:{p_color};color:#000;font-size:0.68rem;'
        f'font-weight:700;padding:2px 8px;border-radius:4px;margin-left:auto">'
        f'{item["priority"]}</span>'
        f'</div>'
        f'<ul style="margin:0;padding-left:18px;font-size:0.82rem">{actions_html}</ul>'
        f'</div>',
        unsafe_allow_html=True,
    )


def render():
    page_header(
        agent_name="Disaster Response Recommendation Agent",
        icon="🛟",
        tagline="Suggests evacuation preparedness, emergency resource allocation, shelter identification, and response strategies.",
        llm="meta-llama/llama-3-3-70b-instruct",
        provider="watsonx",
    )
    how_it_works_panel(
        llm="IBM watsonx · LLaMA 3-70B",
        tools=["get_shelter_locations", "allocate_resources", "plan_evacuation_routes"],
        memory="Short-term session buffer + ChromaDB RAG",
        guardrails="Input, Output, HITL, Operational, Ethical",
        react_steps=3,
        token_budget=3072,
    )

    st.divider()

    # Timeline
    st.markdown("### ⏱️ Response Timeline")
    timeline_data = [
        ("T-72h", "Monitoring enhanced · Resource pre-positioning begins"),
        ("T-48h", "Red alert issued · Evacuation orders activated"),
        ("T-36h", "Mass evacuation begins · Port closure"),
        ("T-24h", "All shelters operational · NDRF deployed"),
        ("T-12h", "Final evacuation sweep · Emergency broadcast"),
        ("T-0h",  "LANDFALL · Search & Rescue on standby"),
        ("T+6h",  "Damage assessment begins · Relief operations"),
        ("T+24h", "Recovery phase · Restoration of services"),
    ]
    tl_html = '<div style="position:relative;padding-left:30px">'
    for time_label, desc in timeline_data:
        color = "#E53935" if "LAND" in desc else "#4FC3F7" if time_label.startswith("T-") else "#81C784"
        tl_html += (
            f'<div style="display:flex;align-items:flex-start;gap:14px;margin-bottom:10px">'
            f'<div style="min-width:52px;font-size:0.78rem;font-weight:700;'
            f'color:{color};padding-top:2px">{time_label}</div>'
            f'<div style="background:#161B22;border:1px solid #30363D;border-radius:8px;'
            f'padding:8px 14px;flex:1;font-size:0.82rem;color:#C9D1D9">{desc}</div>'
            f'</div>'
        )
    tl_html += '</div>'
    st.markdown(tl_html, unsafe_allow_html=True)

    st.divider()
    st.markdown("### 🗂️ Response Action Plan")
    for item in RESPONSE_PLAN:
        _response_card(item)

    st.divider()
    st.markdown("### 🏠 Cyclone Shelter Capacity")
    shelters = pd.DataFrame({
        "District":       ["Visakhapatnam", "Srikakulam", "E. Godavari", "Ganjam", "Puri"],
        "Shelters":       [87, 64, 52, 48, 61],
        "Capacity":       [1200000, 850000, 680000, 580000, 710000],
        "Occupancy %":    [72, 68, 45, 30, 28],
    })
    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=shelters["District"], y=shelters["Capacity"] / 1e5,
        name="Total Capacity (×100K)",
        marker_color="#4FC3F7", opacity=0.85,
    ))
    fig.add_trace(go.Bar(
        x=shelters["District"],
        y=[c * o / 100 / 1e5 for c, o in zip(shelters["Capacity"], shelters["Occupancy %"])],
        name="Current Occupancy",
        marker_color="#E53935", opacity=0.85,
    ))
    fig.update_layout(
        barmode="overlay",
        paper_bgcolor="#161B22", plot_bgcolor="#161B22", height=240,
        margin=dict(l=10, r=10, t=30, b=30),
        xaxis=dict(color="#8B949E"),
        yaxis=dict(title="×100K persons", color="#8B949E", gridcolor="#30363D"),
        legend=dict(bgcolor="#161B22", font=dict(color="#E6EDF3")),
        title=dict(text="Shelter Capacity vs Current Occupancy", font=dict(color="#E6EDF3")),
    )
    st.plotly_chart(fig, use_container_width=True)

    st.divider()
    st.markdown("### 🤖 Agent Output")
    results = st.session_state.get("agent_results", {})
    result_report_card(results.get("response", {}))
    run_agent_button("response", "▶ Run Disaster Response Agent")
