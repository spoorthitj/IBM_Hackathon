"""
Agent 3 — Cyclone Tracking & Prediction Agent detail page.
"""
import streamlit as st
import plotly.graph_objects as go
import numpy as np
from pages.agents._agent_base import (
    page_header, how_it_works_panel, result_report_card, run_agent_button
)

TRACK = [
    (87.5, 12.0, 65),  (87.1, 13.2, 70),  (86.6, 14.5, 82),
    (86.0, 15.8, 88),  (85.3, 17.0, 102), (84.5, 18.1, 108),
    (83.8, 19.2, 120), (83.0, 20.0, 128), (82.3, 20.5, 130),
    (81.5, 20.8, 115), (80.8, 21.0, 105), (80.2, 21.1, 92),
    (79.8, 20.9, 85),
]
# Uncertainty cone (offset tracks)
TRACK_N = [(lon - 0.3 * i/12, lat + 0.2 * i/12, w) for i, (lon, lat, w) in enumerate(TRACK)]
TRACK_S = [(lon + 0.3 * i/12, lat - 0.2 * i/12, w) for i, (lon, lat, w) in enumerate(TRACK)]


def render():
    page_header(
        agent_name="Cyclone Tracking & Prediction Agent",
        icon="🗺️",
        tagline="Predicts cyclone movement, direction, speed, and possible landfall locations.",
        llm="gemini-pro",
        provider="gemini",
    )
    how_it_works_panel(
        llm="Google Gemini Pro",
        tools=["fetch_track_history", "predict_trajectory"],
        memory="Short-term session buffer + ChromaDB RAG",
        guardrails="Input, Output, Operational",
        react_steps=3,
        token_budget=3072,
    )

    st.divider()
    st.markdown("### 📍 72-Hour Track Forecast with Uncertainty Cone")

    lons = [t[0] for t in TRACK]
    lats = [t[1] for t in TRACK]
    winds = [t[2] for t in TRACK]
    hours = [f"T+{i*6}h" for i in range(len(TRACK))]

    fig = go.Figure()

    # Uncertainty cone (filled area)
    cone_lon = [t[0] for t in TRACK_N] + [t[0] for t in reversed(TRACK_S)]
    cone_lat = [t[1] for t in TRACK_N] + [t[1] for t in reversed(TRACK_S)]
    fig.add_trace(go.Scattergeo(
        lon=cone_lon, lat=cone_lat,
        mode="lines",
        fill="toself",
        fillcolor="rgba(229,57,53,0.12)",
        line=dict(color="rgba(229,57,53,0.3)", width=1),
        name="Uncertainty Cone",
        showlegend=True,
    ))

    # Main track line
    fig.add_trace(go.Scattergeo(
        lon=lons, lat=lats,
        mode="lines+markers",
        line=dict(color="#FF6D00", width=3),
        marker=dict(
            size=[8 + w / 20 for w in winds],
            color=winds,
            colorscale=[[0,"#64DD17"],[0.3,"#FFD600"],[0.6,"#FF6D00"],[1.0,"#E53935"]],
            cmin=60, cmax=135,
            colorbar=dict(title="Wind (kt)", titlefont=dict(color="#8B949E"),
                          tickfont=dict(color="#8B949E"), x=1.0),
            showscale=True,
        ),
        text=hours,
        hovertemplate="<b>%{text}</b><br>Lat: %{lat:.1f}°N<br>Lon: %{lon:.1f}°E<extra></extra>",
        name="Forecast Track",
    ))

    # Landfall marker
    fig.add_trace(go.Scattergeo(
        lon=[83.3], lat=[17.7],
        mode="markers+text",
        marker=dict(size=18, color="#E53935", symbol="star", line=dict(color="#FFFFFF", width=2)),
        text=["LANDFALL"], textfont=dict(color="#E53935", size=11),
        textposition="top right",
        name="Predicted Landfall",
    ))

    fig.update_layout(
        geo=dict(
            scope="asia", projection_type="mercator",
            showland=True, landcolor="#1C2333",
            showocean=True, oceancolor="#0A1628",
            showcoastlines=True, coastlinecolor="#2D3A4A",
            showcountries=True, countrycolor="#2D3A4A",
            lonaxis=dict(range=[74, 96]), lataxis=dict(range=[8, 26]),
            bgcolor="#0A1628",
        ),
        paper_bgcolor="#0D1117", height=480,
        margin=dict(l=0, r=0, t=0, b=0),
        font=dict(color="#E6EDF3"),
        legend=dict(bgcolor="#161B22", font=dict(color="#E6EDF3")),
    )
    st.plotly_chart(fig, use_container_width=True)

    # Track table
    st.markdown("#### 📋 Track Forecast Table")
    import pandas as pd
    df = pd.DataFrame({
        "Time":        hours,
        "Latitude (°N)":  [t[1] for t in TRACK],
        "Longitude (°E)": [t[0] for t in TRACK],
        "Max Wind (kt)":  winds,
        "Speed (kt)":  [12 + i * 0.5 for i in range(len(TRACK))],
        "Direction":   ["NNW"] * 5 + ["NW"] * 5 + ["WNW"] * 3,
    })
    st.dataframe(df, use_container_width=True, hide_index=True, height=220)

    st.divider()
    st.markdown("### 🤖 Agent Output")
    results = st.session_state.get("agent_results", {})
    result_report_card(results.get("tracking", {}))
    run_agent_button("tracking", "▶ Run Tracking & Prediction Agent")
