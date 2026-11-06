"""
Observability Dashboard — real-time agent execution traces, token usage, and ReAct logs.
pages/intelligence/observability.py
"""
import streamlit as st
import plotly.graph_objects as go
import pandas as pd
from datetime import datetime, timedelta
import random


AGENT_NAMES = [
    "Weather Analysis", "Cyclone Detection", "Tracking & Prediction",
    "Intensity Prediction", "Impact Assessment", "Early Warning", "Disaster Response"
]

LLM_MAP = {
    "Weather Analysis":     ("watsonx",  "#4FC3F7"),
    "Cyclone Detection":    ("watsonx",  "#4FC3F7"),
    "Tracking & Prediction":("gemini",   "#81C784"),
    "Intensity Prediction": ("groq",     "#FFB74D"),
    "Impact Assessment":    ("gemini",   "#81C784"),
    "Early Warning":        ("groq",     "#FFB74D"),
    "Disaster Response":    ("watsonx",  "#4FC3F7"),
}


def _mock_trace(agent: str, session_id: str = "demo-001") -> dict:
    """Simulate a ReAct execution trace for an agent."""
    llm, _ = LLM_MAP.get(agent, ("demo", "#8B949E"))
    random.seed(hash(agent + session_id) % 2**16)
    steps = []
    step_types = ["Think", "Act", "Observe"]
    for i in range(3):
        st_type = step_types[i % 3]
        steps.append({
            "step": i + 1,
            "type": st_type,
            "content": {
                "Think": f"Analyzing {agent.lower()} data to determine cyclone parameters...",
                "Act":   f"Calling tool: {'get_weather_data' if i == 1 else 'analyze_satellite_image'}",
                "Observe": f"Tool returned: pressure=988hPa, wind=95kt, SST=30.2°C — cyclone signature confirmed",
            }[st_type],
            "tokens_in":  random.randint(180, 420),
            "tokens_out": random.randint(80, 220),
            "latency_ms": random.randint(400, 2200),
        })
    return {
        "agent":       agent,
        "llm":         llm,
        "session_id":  session_id,
        "steps":       steps,
        "total_tokens": sum(s["tokens_in"] + s["tokens_out"] for s in steps),
        "total_latency_ms": sum(s["latency_ms"] for s in steps),
        "confidence":  round(random.uniform(0.82, 0.96), 3),
        "guardrail_blocked": False,
    }


def render():
    st.markdown("## 🔭 Agent Observability Dashboard")
    st.markdown(
        '<p style="color:#8B949E">Full execution trace visibility — ReAct steps, '
        'token usage, latency breakdown, and guardrail events per agent.</p>',
        unsafe_allow_html=True,
    )

    with st.expander("ℹ️ How this works", expanded=False):
        st.markdown("""
**Observability Pipeline:**  
Every agent run emits structured traces captured by `analytics/metrics_tracker.py` (SQLite-backed).  
Each trace includes: ReAct loop steps (Think → Act → Observe), input/output token counts,  
latency per step, tool calls made, guardrail check results, and final confidence score.  

**Memory Visibility:**  
- Short-term: last 5 exchanges in session buffer (`memory/short_term.py`)  
- Long-term: ChromaDB vector store queries logged with similarity scores (`memory/vector_store.py`)
        """)

    st.divider()

    # ── Session selector ──────────────────────────────────────────
    col_sess, col_ref = st.columns([3, 1])
    with col_sess:
        session_id = st.text_input("Session ID", value="demo-001", key="obs_session")
    with col_ref:
        st.markdown("<br>", unsafe_allow_html=True)
        refresh = st.button("🔄 Refresh", use_container_width=True)

    # Attempt to load real traces from metrics tracker
    real_traces = []
    results = st.session_state.get("agent_results", {})
    agent_key_map = {
        "weather": "Weather Analysis", "detection": "Cyclone Detection",
        "tracking": "Tracking & Prediction", "intensity": "Intensity Prediction",
        "impact": "Impact Assessment", "warning": "Early Warning",
        "response": "Disaster Response",
    }
    for key, name in agent_key_map.items():
        r = results.get(key, {})
        if r:
            real_traces.append({
                "agent":             name,
                "llm":               LLM_MAP[name][0],
                "steps":             [],
                "total_tokens":      r.get("tokens_used", 420),
                "total_latency_ms":  r.get("latency_ms", 1200),
                "confidence":        r.get("confidence", 0.88),
                "guardrail_blocked": r.get("guardrails", {}).get("blocked", False),
            })

    traces = real_traces if real_traces else [_mock_trace(a) for a in AGENT_NAMES]

    # ── Pipeline execution timeline ───────────────────────────────
    st.markdown("### 🕐 Pipeline Execution Timeline")
    base_time = datetime.now() - timedelta(minutes=3)
    fig_timeline = go.Figure()
    cursor = 0
    for i, t in enumerate(traces):
        dur_s = t["total_latency_ms"] / 1000
        _, color = LLM_MAP.get(t["agent"], ("demo", "#8B949E"))
        fig_timeline.add_trace(go.Bar(
            x=[dur_s], y=[t["agent"]],
            orientation="h",
            marker_color=color,
            base=cursor,
            showlegend=False,
            hovertemplate=f"<b>{t['agent']}</b><br>Duration: {dur_s:.1f}s<extra></extra>",
        ))
        fig_timeline.add_annotation(
            x=cursor + dur_s / 2, y=t["agent"],
            text=f"{dur_s:.1f}s",
            showarrow=False,
            font=dict(color="#0D1117", size=10, weight="bold"),
        )
        cursor += dur_s + 0.2

    fig_timeline.update_layout(
        paper_bgcolor="#161B22", plot_bgcolor="#161B22", height=300,
        barmode="stack",
        margin=dict(l=10, r=10, t=30, b=20),
        xaxis=dict(title="Time (seconds)", color="#8B949E", gridcolor="#30363D"),
        yaxis=dict(color="#8B949E"),
        title=dict(text="Agent Execution Timeline (Sequential Pipeline)", font=dict(color="#E6EDF3")),
    )
    st.plotly_chart(fig_timeline, use_container_width=True)

    # ── Token usage breakdown ─────────────────────────────────────
    st.markdown("### 💬 Token Usage by Agent")
    col_tok, col_conf = st.columns(2)

    with col_tok:
        fig_tok = go.Figure()
        # Split into rough 2/3 in, 1/3 out
        tok_in  = [int(t["total_tokens"] * 0.65) for t in traces]
        tok_out = [int(t["total_tokens"] * 0.35) for t in traces]
        agents  = [t["agent"] for t in traces]
        fig_tok.add_trace(go.Bar(y=agents, x=tok_in,  orientation="h",
                                 name="Input Tokens",  marker_color="#4FC3F7", opacity=0.85))
        fig_tok.add_trace(go.Bar(y=agents, x=tok_out, orientation="h",
                                 name="Output Tokens", marker_color="#FF6D00", opacity=0.85))
        fig_tok.update_layout(
            barmode="stack",
            paper_bgcolor="#161B22", plot_bgcolor="#161B22", height=300,
            margin=dict(l=10, r=60, t=30, b=20),
            xaxis=dict(title="Tokens", color="#8B949E", gridcolor="#30363D"),
            yaxis=dict(color="#8B949E", tickfont=dict(size=9)),
            legend=dict(bgcolor="#161B22", font=dict(color="#E6EDF3", size=10)),
            title=dict(text="Token Usage per Agent", font=dict(color="#E6EDF3")),
        )
        st.plotly_chart(fig_tok, use_container_width=True)

    with col_conf:
        confs = [t["confidence"] for t in traces]
        colors = ["#69F0AE" if c >= 0.9 else "#FFD600" if c >= 0.8 else "#FF7043" for c in confs]
        fig_conf = go.Figure(go.Bar(
            y=agents, x=confs,
            orientation="h",
            marker_color=colors,
            text=[f"{c:.0%}" for c in confs],
            textposition="outside",
            textfont=dict(color="#E6EDF3"),
        ))
        fig_conf.add_vline(x=0.85, line_dash="dash", line_color="#FFD600",
                           annotation_text="Min threshold", annotation_font_color="#FFD600")
        fig_conf.update_layout(
            paper_bgcolor="#161B22", plot_bgcolor="#161B22", height=300,
            margin=dict(l=10, r=60, t=30, b=20),
            xaxis=dict(range=[0.6, 1.05], title="Confidence", color="#8B949E", gridcolor="#30363D"),
            yaxis=dict(color="#8B949E", tickfont=dict(size=9)),
            title=dict(text="Agent Output Confidence Scores", font=dict(color="#E6EDF3")),
        )
        st.plotly_chart(fig_conf, use_container_width=True)

    st.divider()

    # ── ReAct trace viewer ────────────────────────────────────────
    st.markdown("### 🔄 ReAct Execution Trace Viewer")
    selected_agent = st.selectbox("Select agent to inspect", AGENT_NAMES, key="obs_agent")
    trace = next((t for t in traces if t["agent"] == selected_agent),
                 _mock_trace(selected_agent))

    if trace["steps"]:
        step_colors = {"Think": "#4FC3F7", "Act": "#FFB74D", "Observe": "#81C784"}
        for s in trace["steps"]:
            color = step_colors.get(s["type"], "#8B949E")
            st.markdown(
                f'<div style="background:#161B22;border:1px solid #30363D;'
                f'border-left:4px solid {color};border-radius:8px;'
                f'padding:10px 16px;margin-bottom:8px">'
                f'<div style="display:flex;align-items:center;gap:8px;margin-bottom:4px">'
                f'<span style="background:{color};color:#000;font-size:0.7rem;'
                f'font-weight:700;padding:2px 8px;border-radius:4px">'
                f'Step {s["step"]}: {s["type"]}</span>'
                f'<span style="color:#8B949E;font-size:0.72rem">'
                f'Tokens: {s["tokens_in"]}↓ {s["tokens_out"]}↑ · {s["latency_ms"]}ms</span>'
                f'</div>'
                f'<div style="color:#C9D1D9;font-size:0.82rem">{s["content"]}</div>'
                f'</div>',
                unsafe_allow_html=True,
            )
    else:
        st.info(f"Run the pipeline to see real ReAct traces for {selected_agent}.")
        # Show mock trace
        mock = _mock_trace(selected_agent)
        for s in mock["steps"]:
            step_colors = {"Think": "#4FC3F7", "Act": "#FFB74D", "Observe": "#81C784"}
            color = step_colors.get(s["type"], "#8B949E")
            st.markdown(
                f'<div style="background:#161B22;border:1px solid #30363D;'
                f'border-left:4px solid {color};border-radius:8px;'
                f'padding:10px 16px;margin-bottom:8px">'
                f'<div style="display:flex;align-items:center;gap:8px;margin-bottom:4px">'
                f'<span style="background:{color};color:#000;font-size:0.7rem;'
                f'font-weight:700;padding:2px 8px;border-radius:4px">'
                f'Step {s["step"]}: {s["type"]}</span>'
                f'<span style="color:#8B949E;font-size:0.72rem">'
                f'Tokens: {s["tokens_in"]}↓ {s["tokens_out"]}↑ · {s["latency_ms"]}ms</span>'
                f'</div>'
                f'<div style="color:#C9D1D9;font-size:0.82rem">{s["content"]}</div>'
                f'</div>',
                unsafe_allow_html=True,
            )

    # ── Memory state ──────────────────────────────────────────────
    st.divider()
    st.markdown("### 🗄️ Memory State")
    mem_col1, mem_col2 = st.columns(2)

    with mem_col1:
        st.markdown("**Short-Term Buffer (Session)**")
        buffer_items = [
            "Weather agent: pressure 988hPa, wind 95kt, SST 30.2°C → ALERT",
            "Detection agent: cyclone probability 94.3% at 12°N, 87.5°E",
            "Tracking agent: landfall T+48h near Visakhapatnam (confidence 0.89)",
            "Intensity agent: RI detected, peak 130kt at T+48h",
            "Impact agent: 1.95M at risk, 3 high-risk districts",
        ]
        for i, item in enumerate(buffer_items):
            st.markdown(
                f'<div style="background:#161B22;border:1px solid #30363D;'
                f'border-radius:6px;padding:6px 12px;margin-bottom:4px;'
                f'font-size:0.78rem;color:#C9D1D9">'
                f'<span style="color:#4FC3F7;font-weight:600">[{i+1}]</span> {item}'
                f'</div>',
                unsafe_allow_html=True,
            )

    with mem_col2:
        st.markdown("**Long-Term Vector Store (ChromaDB)**")
        rag_hits = [
            ("Historical cyclone PHAILIN (2013) track", 0.91),
            ("Bay of Bengal cyclogenesis conditions", 0.88),
            ("NDMA evacuation guidelines Cat 4+", 0.85),
            ("Visakhapatnam storm surge risk zones", 0.83),
            ("Rapid intensification case studies BOB", 0.79),
        ]
        for doc, score in rag_hits:
            st.markdown(
                f'<div style="background:#161B22;border:1px solid #30363D;'
                f'border-radius:6px;padding:6px 12px;margin-bottom:4px;'
                f'display:flex;justify-content:space-between;'
                f'font-size:0.78rem;color:#C9D1D9">'
                f'<span>{doc}</span>'
                f'<span style="color:#81C784;font-weight:600;min-width:36px;text-align:right">'
                f'{score:.2f}</span>'
                f'</div>',
                unsafe_allow_html=True,
            )
