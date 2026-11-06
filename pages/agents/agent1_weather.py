"""
Agent 1 — Weather Data Analysis Agent detail page.
"""
import streamlit as st
import plotly.graph_objects as go
import numpy as np
from pages.agents._agent_base import (
    page_header, how_it_works_panel, result_report_card, run_agent_button
)


def render():
    page_header(
        agent_name="Weather Data Analysis Agent",
        icon="🌦️",
        tagline="Analyzes atmospheric pressure, wind speed, humidity, rainfall, and sea surface temperature.",
        llm="meta-llama/llama-3-3-70b-instruct",
        provider="watsonx",
    )
    how_it_works_panel(
        llm="IBM watsonx · LLaMA 3-70B",
        tools=["get_weather_data", "fetch_sst_data"],
        memory="Short-term session buffer + ChromaDB RAG",
        guardrails="Input, Output, Data, Operational, Ethical",
        react_steps=3,
        token_budget=2048,
    )

    st.divider()

    # ── Live weather data visualization ──────────────────────────
    st.markdown("### 📊 Current Meteorological Readings")

    # Synthetic data for Bay of Bengal transect
    lats = np.linspace(8, 22, 15)
    pressure = 1010 - np.exp((lats - 13) * 0.3) * 18
    wind_kt   = 20 + np.exp((lats - 13) * 0.4) * 30
    humidity  = 70 + np.sin((lats - 8) * 0.5) * 15
    sst       = 29 + np.sin((lats - 10) * 0.3) * 1.5

    col_p, col_w = st.columns(2)
    with col_p:
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=lats, y=pressure,
            mode="lines+markers",
            line=dict(color="#4FC3F7", width=2),
            marker=dict(size=6, color="#4FC3F7"),
            fill="tozeroy",
            fillcolor="rgba(79,195,247,0.08)",
            name="Pressure (hPa)",
        ))
        fig.update_layout(
            paper_bgcolor="#161B22", plot_bgcolor="#161B22", height=220,
            margin=dict(l=10, r=10, t=30, b=30),
            xaxis=dict(title="Latitude °N", color="#8B949E", gridcolor="#30363D"),
            yaxis=dict(title="hPa", color="#8B949E", gridcolor="#30363D"),
            title=dict(text="Atmospheric Pressure (Bay of Bengal)", font=dict(color="#E6EDF3")),
        )
        st.plotly_chart(fig, use_container_width=True)

    with col_w:
        fig2 = go.Figure()
        fig2.add_trace(go.Scatter(
            x=lats, y=wind_kt,
            mode="lines+markers",
            line=dict(color="#E53935", width=2),
            marker=dict(size=6, color="#E53935"),
            fill="tozeroy",
            fillcolor="rgba(229,57,53,0.08)",
            name="Wind (kt)",
        ))
        fig2.update_layout(
            paper_bgcolor="#161B22", plot_bgcolor="#161B22", height=220,
            margin=dict(l=10, r=10, t=30, b=30),
            xaxis=dict(title="Latitude °N", color="#8B949E", gridcolor="#30363D"),
            yaxis=dict(title="Knots", color="#8B949E", gridcolor="#30363D"),
            title=dict(text="Wind Speed (Bay of Bengal)", font=dict(color="#E6EDF3")),
        )
        st.plotly_chart(fig2, use_container_width=True)

    col_h, col_s = st.columns(2)
    with col_h:
        fig3 = go.Figure(go.Bar(
            x=lats, y=humidity,
            marker_color=[f"rgba(129,199,132,{0.4 + h/200})" for h in humidity],
        ))
        fig3.update_layout(
            paper_bgcolor="#161B22", plot_bgcolor="#161B22", height=200,
            margin=dict(l=10, r=10, t=30, b=30),
            xaxis=dict(title="Latitude °N", color="#8B949E", gridcolor="#30363D"),
            yaxis=dict(title="%", color="#8B949E", gridcolor="#30363D"),
            title=dict(text="Relative Humidity (%)", font=dict(color="#E6EDF3")),
        )
        st.plotly_chart(fig3, use_container_width=True)

    with col_s:
        fig4 = go.Figure(go.Scatter(
            x=lats, y=sst,
            mode="lines+markers",
            line=dict(color="#FFD600", width=2),
            marker=dict(size=6, color="#FFD600"),
            fill="tozeroy",
            fillcolor="rgba(255,214,0,0.08)",
        ))
        fig4.add_hline(y=26.5, line_dash="dash", line_color="#FF6D00",
                       annotation_text="Cyclogenesis threshold (26.5°C)",
                       annotation_font_color="#FF6D00")
        fig4.update_layout(
            paper_bgcolor="#161B22", plot_bgcolor="#161B22", height=200,
            margin=dict(l=10, r=10, t=30, b=30),
            xaxis=dict(title="Latitude °N", color="#8B949E", gridcolor="#30363D"),
            yaxis=dict(title="°C", color="#8B949E", gridcolor="#30363D"),
            title=dict(text="Sea Surface Temperature (°C)", font=dict(color="#E6EDF3")),
        )
        st.plotly_chart(fig4, use_container_width=True)

    st.divider()
    st.markdown("### 🤖 Agent Output")
    results = st.session_state.get("agent_results", {})
    result_report_card(results.get("weather", {}))
    run_agent_button("weather", "▶ Run Weather Analysis Agent")
