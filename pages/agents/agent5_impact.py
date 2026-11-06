"""
Agent 5 — Impact Assessment Agent detail page.
"""
import streamlit as st
import plotly.graph_objects as go
import pandas as pd
from pages.agents._agent_base import (
    page_header, how_it_works_panel, result_report_card, run_agent_button
)

IMPACT_ZONES = [
    {"district": "Visakhapatnam", "state": "Andhra Pradesh", "pop_risk": 890000,
     "risk": 95, "infrastructure": 88, "agriculture": 72, "coastal_flood": 98, "color": "#E53935"},
    {"district": "Srikakulam",    "state": "Andhra Pradesh", "pop_risk": 320000,
     "risk": 87, "infrastructure": 75, "agriculture": 80, "coastal_flood": 90, "color": "#FF6D00"},
    {"district": "East Godavari", "state": "Andhra Pradesh", "pop_risk": 280000,
     "risk": 78, "infrastructure": 65, "agriculture": 88, "coastal_flood": 82, "color": "#FF6D00"},
    {"district": "Ganjam",        "state": "Odisha",         "pop_risk": 190000,
     "risk": 65, "infrastructure": 55, "agriculture": 70, "coastal_flood": 68, "color": "#FFD600"},
    {"district": "Puri",          "state": "Odisha",         "pop_risk": 150000,
     "risk": 60, "infrastructure": 50, "agriculture": 65, "coastal_flood": 72, "color": "#FFD600"},
    {"district": "Prakasam",      "state": "Andhra Pradesh", "pop_risk": 120000,
     "risk": 45, "infrastructure": 40, "agriculture": 55, "coastal_flood": 48, "color": "#64DD17"},
]


def render():
    page_header(
        agent_name="Impact Assessment Agent",
        icon="⚠️",
        tagline="Identifies vulnerable coastal regions and assesses potential risks to population, infrastructure, and agriculture.",
        llm="gemini-pro",
        provider="gemini",
    )
    how_it_works_panel(
        llm="Google Gemini Pro",
        tools=["calculate_impact_score", "fetch_population_data", "get_elevation_data"],
        memory="Short-term session buffer + ChromaDB RAG",
        guardrails="Input, Output, Data, Ethical",
        react_steps=3,
        token_budget=3072,
    )

    st.divider()
    st.markdown("### 🗺️ District Impact Assessment")

    # KPI summary
    total_at_risk = sum(z["pop_risk"] for z in IMPACT_ZONES)
    k1, k2, k3, k4 = st.columns(4)
    for col, lbl, val, c in [
        (k1, "Population at Risk",   f"{total_at_risk/1e6:.2f}M", "#E53935"),
        (k2, "High-Risk Districts",  "3",                          "#FF6D00"),
        (k3, "Flood-Prone Villages", "847",                        "#FFD600"),
        (k4, "Critical Infra. at Risk", "214 sites",              "#4FC3F7"),
    ]:
        with col:
            st.markdown(
                f'<div style="background:#161B22;border:1px solid #30363D;border-radius:8px;'
                f'padding:12px;text-align:center">'
                f'<div style="font-weight:700;color:{c};font-size:1.2rem">{val}</div>'
                f'<div style="font-size:0.7rem;color:#8B949E;text-transform:uppercase">{lbl}</div>'
                f'</div>',
                unsafe_allow_html=True,
            )

    st.markdown("<br>", unsafe_allow_html=True)

    col_bar, col_map = st.columns(2)
    with col_bar:
        df = pd.DataFrame(IMPACT_ZONES)
        fig = go.Figure()
        for metric, color, name in [
            ("risk", "#E53935", "Overall Risk"),
            ("infrastructure", "#4FC3F7", "Infrastructure"),
            ("agriculture", "#81C784", "Agriculture"),
            ("coastal_flood", "#FFD600", "Coastal Flood"),
        ]:
            fig.add_trace(go.Bar(
                name=name,
                x=df["district"],
                y=df[metric],
                marker_color=color,
                opacity=0.85,
            ))
        fig.update_layout(
            barmode="group",
            paper_bgcolor="#161B22", plot_bgcolor="#161B22", height=320,
            margin=dict(l=10, r=10, t=30, b=60),
            xaxis=dict(color="#8B949E", tickangle=30, tickfont=dict(size=9)),
            yaxis=dict(title="Risk Score (0–100)", color="#8B949E", gridcolor="#30363D"),
            legend=dict(bgcolor="#161B22", font=dict(color="#E6EDF3", size=10)),
            title=dict(text="Multi-Sector Risk by District", font=dict(color="#E6EDF3")),
        )
        st.plotly_chart(fig, use_container_width=True)

    with col_map:
        # Scatter geo risk map
        fig2 = go.Figure(go.Scattergeo(
            lon=[83.3, 84.1, 82.3, 85.1, 85.8, 80.6],
            lat=[17.7, 18.3, 16.7, 19.4, 19.8, 15.5],
            mode="markers+text",
            marker=dict(
                size=[z["risk"] / 5 for z in IMPACT_ZONES],
                color=[z["color"] for z in IMPACT_ZONES],
                opacity=0.85,
                line=dict(color="#FFFFFF", width=1),
            ),
            text=[z["district"] for z in IMPACT_ZONES],
            textfont=dict(color="#E6EDF3", size=9),
            textposition="top right",
            hovertemplate="<b>%{text}</b><br>Risk: %{marker.size:.0f}%<extra></extra>",
        ))
        fig2.update_layout(
            geo=dict(
                scope="asia", projection_type="mercator",
                showland=True, landcolor="#1C2333",
                showocean=True, oceancolor="#0A1628",
                showcoastlines=True, coastlinecolor="#2D3A4A",
                lonaxis=dict(range=[78, 90]), lataxis=dict(range=[13, 23]),
                bgcolor="#0A1628",
            ),
            paper_bgcolor="#0D1117", height=320,
            margin=dict(l=0, r=0, t=30, b=0),
            title=dict(text="Coastal Risk Zone Map", font=dict(color="#E6EDF3")),
        )
        st.plotly_chart(fig2, use_container_width=True)

    # District table
    st.markdown("#### 📋 District Impact Summary")
    disp = pd.DataFrame(IMPACT_ZONES)[
        ["district","state","pop_risk","risk","infrastructure","agriculture","coastal_flood"]
    ].rename(columns={
        "district":"District", "state":"State", "pop_risk":"Pop. at Risk",
        "risk":"Overall Risk%", "infrastructure":"Infra%",
        "agriculture":"Agri%", "coastal_flood":"Flood%",
    })
    st.dataframe(disp, use_container_width=True, hide_index=True)

    st.divider()
    st.markdown("### 🤖 Agent Output")
    results = st.session_state.get("agent_results", {})
    result_report_card(results.get("impact", {}))
    run_agent_button("impact", "▶ Run Impact Assessment Agent")
