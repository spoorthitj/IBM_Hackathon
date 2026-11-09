
"""
Agent 2 — Cyclone Detection Agent detail page.
"""
import streamlit as st
import plotly.graph_objects as go
import numpy as np

from pages.agents._agent_base import (
    page_header,
    how_it_works_panel,
    result_report_card,
    run_agent_button,
)


def render():
    page_header(
        agent_name="Cyclone Detection Agent",
        icon="🔍",
        tagline="Identifies potential cyclone formations by analyzing satellite imagery and changing weather patterns.",
        llm="meta-llama/llama-3-3-70b-instruct",
        provider="watsonx",
    )

    how_it_works_panel(
        llm="IBM watsonx · LLaMA 3-70B",
        tools=["analyze_satellite_image", "detect_convective_pattern"],
        memory="Short-term session buffer + ChromaDB RAG",
        guardrails="Input, Output, Security, Operational",
        react_steps=3,
        token_budget=2048,
    )

    st.divider()
    st.markdown("### 🛰️ Satellite Cloud Pattern Analysis")

    # Simulated satellite brightness temperature
    # Lower temperatures indicate colder cloud tops and deep convection.
    np.random.seed(42)

    lon_grid = np.linspace(84, 91, 50)
    lat_grid = np.linspace(9, 17, 50)

    lon2d, lat2d = np.meshgrid(lon_grid, lat_grid)

    # Deep convective core centered at 87.5°E, 12.0°N
    brightness_temp = (
        260
        + 40 * (
            1 - np.exp(
                -0.4 * (
                    (lon2d - 87.5) ** 2
                    + (lat2d - 12.0) ** 2
                )
            )
        )
        + np.random.normal(0, 3, lon2d.shape)
    )

    col_sat, col_det = st.columns(2)

    # Satellite heatmap
    with col_sat:
        fig = go.Figure(
            go.Heatmap(
                z=brightness_temp,
                x=lon_grid,
                y=lat_grid,
                colorscale=[
                    [0.0, "#880E4F"],
                    [0.2, "#E53935"],
                    [0.4, "#FF6D00"],
                    [0.6, "#FFD600"],
                    [0.8, "#4FC3F7"],
                    [1.0, "#E6EDF3"],
                ],
                colorbar=dict(
                    title=dict(
                        text="Brightness Temp (K)",
                        font=dict(color="#8B949E"),
                    ),
                    tickfont=dict(color="#8B949E"),
                ),
                zmin=255,
                zmax=300,
                reversescale=True,
            )
        )

        # Mark cyclone center
        fig.add_trace(
            go.Scatter(
                x=[87.5],
                y=[12.0],
                mode="markers",
                marker=dict(
                    size=14,
                    color="#FFFFFF",
                    symbol="circle-open",
                    line=dict(width=2),
                ),
                name="Cyclone Eye",
                showlegend=False,
            )
        )

        fig.update_layout(
            paper_bgcolor="#161B22",
            plot_bgcolor="#161B22",
            height=300,
            margin=dict(l=10, r=10, t=30, b=10),
            xaxis=dict(
                title="Longitude °E",
                color="#8B949E",
                gridcolor="#30363D",
            ),
            yaxis=dict(
                title="Latitude °N",
                color="#8B949E",
                gridcolor="#30363D",
            ),
            title=dict(
                text="IR Brightness Temperature (K) — T+0h",
                font=dict(color="#E6EDF3"),
            ),
        )

        st.plotly_chart(fig, use_container_width=True)

    # Detection confidence chart
    with col_det:
        features = [
            "Circular Circulation",
            "Low Pressure Core",
            "Warm Core",
            "Deep Convection",
            "Eye Formation",
            "Spiral Bands",
        ]

        scores = [0.92, 0.88, 0.95, 0.91, 0.79, 0.84]

        colors = [
            "#69F0AE" if score >= 0.85
            else "#FFD600" if score >= 0.7
            else "#FF7043"
            for score in scores
        ]

        fig2 = go.Figure(
            go.Bar(
                y=features,
                x=scores,
                orientation="h",
                marker_color=colors,
                text=[f"{score:.0%}" for score in scores],
                textposition="outside",
                textfont=dict(color="#E6EDF3"),
            )
        )

        fig2.add_vline(
            x=0.80,
            line_dash="dash",
            line_color="#FFD600",
            annotation_text="Detection threshold",
            annotation_font_color="#FFD600",
        )

        fig2.update_layout(
            paper_bgcolor="#161B22",
            plot_bgcolor="#161B22",
            height=300,
            margin=dict(l=0, r=60, t=30, b=10),
            xaxis=dict(
                range=[0, 1.1],
                title="Confidence Score",
                color="#8B949E",
                gridcolor="#30363D",
            ),
            yaxis=dict(color="#8B949E"),
            title=dict(
                text="Feature Detection Confidence",
                font=dict(color="#E6EDF3"),
            ),
        )

        st.plotly_chart(fig2, use_container_width=True)

    # Detection summary
    st.markdown(
        '<div style="background:#0D2818;border:1px solid #69F0AE;'
        'border-radius:10px;padding:14px 18px;margin:10px 0">'
        '<strong style="color:#69F0AE">✅ CYCLONE DETECTED</strong>'
        '<br><span style="color:#E6EDF3;font-size:0.88rem">'
        'Probability: <strong>94.3%</strong> · '
        'Center: 12.0°N, 87.5°E · '
        'System: Pre-Depression → Deep Depression → Cyclonic Storm · '
        'Confidence: <strong>HIGH</strong>'
        '</span></div>',
        unsafe_allow_html=True,
    )

    st.divider()
    st.markdown("### 🤖 Agent Output")

    results = st.session_state.get("agent_results", {})

    result_report_card(results.get("detection", {}))

    run_agent_button(
        "detection",
        "▶ Run Cyclone Detection Agent",
    )
