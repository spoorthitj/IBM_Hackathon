"""
Agent 4 — Cyclone Intensity Prediction Agent detail page.
"""
import streamlit as st
import plotly.graph_objects as go
import numpy as np
from pages.agents._agent_base import (
    page_header, how_it_works_panel, result_report_card, run_agent_button
)

HOURS = list(range(0, 78, 6))
WIND  = [65, 70, 82, 88, 102, 108, 120, 128, 130, 115, 105, 92, 85]
PRESS = [1002, 999, 995, 992, 985, 981, 975, 970, 968, 972, 976, 980, 983]
CAT_LABELS = {65:"TS", 70:"TS", 82:"SCS", 88:"SCS", 102:"VSCS",
              108:"VSCS", 120:"ESCS", 128:"ESCS", 130:"ESCS",
              115:"VSCS", 105:"VSCS", 92:"SCS", 85:"SCS"}


def render():
    page_header(
        agent_name="Cyclone Intensity Prediction Agent",
        icon="💥",
        tagline="Estimates potential cyclone intensity and identifies the possibility of rapid intensification.",
        llm="llama3-70b-8192",
        provider="groq",
    )
    how_it_works_panel(
        llm="Groq Cloud · LLaMA 3-70B",
        tools=["get_sst_profile", "calculate_vws", "compute_ri_index"],
        memory="Short-term session buffer + ChromaDB RAG",
        guardrails="Input, Output, Operational, Ethical",
        react_steps=3,
        token_budget=2048,
    )

    st.divider()
    st.markdown("### ⚡ 72-Hour Intensity Forecast")

    col_wind, col_press = st.columns(2)

    with col_wind:
        cat_colors = {
            "TS":   "#64DD17", "SCS": "#FFD600",
            "VSCS": "#FF6D00", "ESCS": "#E53935",
        }
        marker_colors = [cat_colors.get(CAT_LABELS.get(w, "TS"), "#8B949E") for w in WIND]

        fig = go.Figure()
        # Rapid intensification zone highlight
        fig.add_vrect(x0=24, x1=48, fillcolor="rgba(229,57,53,0.07)",
                      line_width=0, annotation_text="RI Window",
                      annotation_font_color="#E53935")
        fig.add_trace(go.Scatter(
            x=HOURS, y=WIND,
            mode="lines+markers",
            line=dict(color="#E53935", width=3),
            marker=dict(size=10, color=marker_colors, line=dict(color="#FFFFFF", width=1)),
            fill="tozeroy",
            fillcolor="rgba(229,57,53,0.08)",
            hovertemplate="T+%{x}h  Wind: %{y} kt<extra></extra>",
        ))
        fig.add_hline(y=119, line_dash="dot", line_color="#880E4F",
                      annotation_text="ESCS threshold (119kt)", annotation_font_color="#880E4F")
        fig.add_hline(y=89, line_dash="dot", line_color="#FF6D00",
                      annotation_text="VSCS threshold (89kt)", annotation_font_color="#FF6D00")
        fig.update_layout(
            paper_bgcolor="#161B22", plot_bgcolor="#161B22", height=280,
            margin=dict(l=10, r=10, t=30, b=30),
            xaxis=dict(title="Hours", color="#8B949E", gridcolor="#30363D"),
            yaxis=dict(title="Max Wind (kt)", color="#8B949E", gridcolor="#30363D"),
            title=dict(text="Max Sustained Wind Forecast (kt)", font=dict(color="#E6EDF3")),
        )
        st.plotly_chart(fig, use_container_width=True)

    with col_press:
        fig2 = go.Figure(go.Scatter(
            x=HOURS, y=PRESS,
            mode="lines+markers",
            line=dict(color="#4FC3F7", width=3),
            marker=dict(size=8, color="#4FC3F7"),
            fill="tozeroy",
            fillcolor="rgba(79,195,247,0.08)",
            hovertemplate="T+%{x}h  Pressure: %{y} hPa<extra></extra>",
        ))
        fig2.add_hline(y=944, line_dash="dot", line_color="#E53935",
                       annotation_text="ESCS min pressure", annotation_font_color="#E53935")
        fig2.update_layout(
            paper_bgcolor="#161B22", plot_bgcolor="#161B22", height=280,
            margin=dict(l=10, r=10, t=30, b=30),
            xaxis=dict(title="Hours", color="#8B949E", gridcolor="#30363D"),
            yaxis=dict(title="Central Pressure (hPa)", color="#8B949E",
                       gridcolor="#30363D", autorange="reversed"),
            title=dict(text="Central Pressure Forecast (hPa)", font=dict(color="#E6EDF3")),
        )
        st.plotly_chart(fig2, use_container_width=True)

    # RI Alert
    st.markdown(
        '<div style="background:#1A0D00;border:1px solid #FF6D00;border-radius:10px;'
        'padding:14px 18px;margin:10px 0">'
        '<strong style="color:#FF6D00">⚡ RAPID INTENSIFICATION DETECTED</strong>'
        '<br><span style="color:#E6EDF3;font-size:0.88rem">'
        'Wind increase of <strong>35 kt in 24h</strong> (T+12h to T+36h). '
        'Warm SST (30.2°C), low vertical wind shear (8 kt), moist mid-levels. '
        'Peak intensity: <strong>130 kt (ESCS-4)</strong> at T+48h.'
        '</span>'
        '</div>',
        unsafe_allow_html=True,
    )

    st.divider()
    st.markdown("### 🤖 Agent Output")
    results = st.session_state.get("agent_results", {})
    result_report_card(results.get("intensity", {}))
    run_agent_button("intensity", "▶ Run Intensity Prediction Agent")
