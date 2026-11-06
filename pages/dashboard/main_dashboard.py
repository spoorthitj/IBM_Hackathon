"""
Main Mission-Control Dashboard — animated cyclone map + 5 KPIs + agent pipeline status.
pages/dashboard/main_dashboard.py
"""
import streamlit as st
import plotly.graph_objects as go
import numpy as np
import math
import random
from datetime import datetime, timedelta


# ── Cyclone track data (72-hour forecast) ─────────────────────────────────────
TRACK = [
    # (lon, lat, intensity_cat, wind_kt, name_label)
    (87.5, 12.0, 1, 65,  "T+0h"),
    (87.1, 13.2, 1, 70,  "T+6h"),
    (86.6, 14.5, 2, 82,  "T+12h"),
    (86.0, 15.8, 2, 88,  "T+18h"),
    (85.3, 17.0, 3, 102, "T+24h"),
    (84.5, 18.1, 3, 108, "T+30h"),
    (83.8, 19.2, 4, 120, "T+36h"),
    (83.0, 20.0, 4, 128, "T+42h"),
    (82.3, 20.5, 4, 130, "T+48h"),
    (81.5, 20.8, 3, 115, "T+54h"),
    (80.8, 21.0, 3, 105, "T+60h"),
    (80.2, 21.1, 2, 92,  "T+66h"),
    (79.8, 20.9, 2, 85,  "T+72h"),
]

CAT_COLOR = {
    0: "#4FC3F7",   # TD  — light blue
    1: "#64DD17",   # TS  — green
    2: "#FFD600",   # Cat1 — yellow
    3: "#FF6D00",   # Cat2 — orange
    4: "#E53935",   # Cat3 — red
    5: "#880E4F",   # Cat4 — maroon
}

CAT_LABEL = {0:"TD", 1:"TS", 2:"SCS", 3:"VSCS", 4:"ESCS", 5:"SuCS"}

# Indian-coastline reference cities
CITIES = [
    ("Chennai",        80.27, 13.08),
    ("Visakhapatnam",  83.30, 17.69),
    ("Bhubaneswar",    85.82, 20.30),
    ("Kolkata",        88.36, 22.57),
    ("Paradip",        86.61, 20.32),
    ("Puri",           85.83, 19.80),
]


def _intensity_color(cat: int) -> str:
    return CAT_COLOR.get(cat, "#8B949E")


def _spiral_rings(cx: float, cy: float, cat: int, alpha: float = 0.18):
    """Return list of Scattergeo traces forming rotating spiral wind bands."""
    traces = []
    base_radii = [0.4, 0.8, 1.3, 1.9]
    color = CAT_COLOR.get(cat, "#E53935")

    for r in base_radii[:max(cat, 1) + 1]:
        theta = np.linspace(0, 2 * math.pi, 80)
        lons = cx + r * np.cos(theta)
        lats = cy + r * np.sin(theta)
        traces.append(go.Scattergeo(
            lon=lons.tolist(), lat=lats.tolist(),
            mode="lines",
            line=dict(color=color, width=max(1, cat - 1)),
            opacity=alpha,
            showlegend=False,
            hoverinfo="skip",
        ))
    return traces


def _build_animated_figure() -> go.Figure:
    """Build a Plotly figure with animation frames — cyclone track draws itself."""
    n = len(TRACK)
    frames = []

    for frame_i in range(1, n + 1):
        subset = TRACK[:frame_i]
        cur = TRACK[frame_i - 1]
        cx, cy, cat, wind, label = cur

        frame_data = []

        # — Spiral wind rings around current eye
        frame_data.extend(_spiral_rings(cx, cy, cat))

        # — Track line so far
        lons = [t[0] for t in subset]
        lats = [t[1] for t in subset]
        frame_data.append(go.Scattergeo(
            lon=lons, lat=lats,
            mode="lines",
            line=dict(color="#FF6D00", width=2.5, dash="solid"),
            showlegend=False,
            hoverinfo="skip",
        ))

        # — Past track dots
        frame_data.append(go.Scattergeo(
            lon=[t[0] for t in subset[:-1]],
            lat=[t[1] for t in subset[:-1]],
            mode="markers",
            marker=dict(
                size=[6] * len(subset[:-1]),
                color=[CAT_COLOR.get(t[2], "#8B949E") for t in subset[:-1]],
                opacity=0.6,
            ),
            showlegend=False,
            hoverinfo="skip",
        ))

        # — Cyclone eye (pulsing — achieved via size scaling per frame)
        pulse_size = 18 + 6 * math.sin(frame_i * 0.9)
        frame_data.append(go.Scattergeo(
            lon=[cx], lat=[cy],
            mode="markers+text",
            marker=dict(
                size=pulse_size,
                color=CAT_COLOR.get(cat, "#E53935"),
                symbol="circle",
                opacity=0.9,
                line=dict(color="#FFFFFF", width=2),
            ),
            text=[f"🌀 VARUNA\n{CAT_LABEL[cat]} · {wind}kt"],
            textfont=dict(color="#E6EDF3", size=11),
            textposition="top center",
            showlegend=False,
            hovertemplate=(
                f"<b>CYCLONE VARUNA</b><br>"
                f"Position: {cy:.1f}°N, {cx:.1f}°E<br>"
                f"Category: {CAT_LABEL[cat]}<br>"
                f"Wind: {wind} kt<br>"
                f"Time: {label}<extra></extra>"
            ),
        ))

        # — City markers
        frame_data.append(go.Scattergeo(
            lon=[c[1] for c in CITIES],
            lat=[c[2] for c in CITIES],
            mode="markers+text",
            marker=dict(size=7, color="#8B949E", symbol="circle"),
            text=[c[0] for c in CITIES],
            textfont=dict(color="#8B949E", size=9),
            textposition="top right",
            showlegend=False,
            hoverinfo="text",
            hovertext=[c[0] for c in CITIES],
        ))

        frames.append(go.Frame(
            data=frame_data,
            name=label,
            layout=go.Layout(
                annotations=[dict(
                    x=0.01, y=0.98, xref="paper", yref="paper",
                    text=f"⏱ {label}  |  Cat: {CAT_LABEL[cat]}  |  Wind: {wind} kt",
                    showarrow=False,
                    font=dict(color="#E6EDF3", size=13),
                    bgcolor="#161B22",
                    bordercolor=CAT_COLOR.get(cat, "#E53935"),
                    borderwidth=1,
                    borderpad=6,
                    align="left",
                )],
            )
        ))

    # ── Initial static figure (frame 0) ──────────────────────────
    fig = go.Figure(
        data=frames[0].data,
        frames=frames,
        layout=go.Layout(
            geo=dict(
                scope="asia",
                projection_type="mercator",
                showland=True,  landcolor="#1C2333",
                showocean=True, oceancolor="#0A1628",
                showcoastlines=True, coastlinecolor="#2D3A4A",
                showcountries=True, countrycolor="#2D3A4A",
                showrivers=False,
                lonaxis=dict(range=[70, 100]),
                lataxis=dict(range=[5, 30]),
                bgcolor="#0A1628",
            ),
            paper_bgcolor="#0D1117",
            plot_bgcolor="#0D1117",
            margin=dict(l=0, r=0, t=0, b=0),
            height=520,
            font=dict(color="#E6EDF3"),
            updatemenus=[dict(
                type="buttons",
                showactive=True,
                x=0.01, y=0.04, xanchor="left",
                buttons=[
                    dict(
                        label="▶  Play",
                        method="animate",
                        args=[None, dict(
                            frame=dict(duration=650, redraw=True),
                            fromcurrent=True,
                            transition=dict(duration=300, easing="linear"),
                        )],
                    ),
                    dict(
                        label="⏸  Pause",
                        method="animate",
                        args=[[None], dict(
                            frame=dict(duration=0, redraw=False),
                            mode="immediate",
                            transition=dict(duration=0),
                        )],
                    ),
                ],
                font=dict(color="#E6EDF3"),
                bgcolor="#161B22",
                bordercolor="#30363D",
            )],
            sliders=[dict(
                active=0,
                currentvalue=dict(
                    prefix="Forecast: ",
                    font=dict(color="#E6EDF3", size=12),
                    visible=True,
                    xanchor="center",
                ),
                pad=dict(t=10, b=0),
                bgcolor="#161B22",
                bordercolor="#30363D",
                font=dict(color="#8B949E", size=10),
                tickcolor="#8B949E",
                steps=[
                    dict(
                        args=[[f.name], dict(
                            frame=dict(duration=650, redraw=True),
                            mode="immediate",
                            transition=dict(duration=300),
                        )],
                        label=f.name,
                        method="animate",
                    )
                    for f in frames
                ],
            )],
        ),
    )
    return fig


def _kpi(col, icon, label, value, delta, color):
    with col:
        delta_html = f'<div style="font-size:0.72rem;color:#69F0AE;margin-top:2px">{delta}</div>' if delta else ""
        st.markdown(
            f'<div style="background:#161B22;border:1px solid #30363D;border-radius:12px;'
            f'padding:16px 12px;text-align:center;margin-bottom:4px">'
            f'<div style="font-size:1.6rem">{icon}</div>'
            f'<div style="font-size:1.5rem;font-weight:700;color:{color};line-height:1.1">{value}</div>'
            f'<div style="font-size:0.7rem;color:#8B949E;text-transform:uppercase;'
            f'letter-spacing:0.07em;margin-top:4px">{label}</div>'
            f'{delta_html}'
            f'</div>',
            unsafe_allow_html=True,
        )


def _agent_pill(name: str, status: str, color: str, llm: str):
    icon = {"COMPLETE": "✅", "RUNNING": "⚙️", "PENDING": "⬜", "BLOCKED": "🔴"}.get(status, "⬜")
    return (
        f'<div style="display:flex;align-items:center;gap:8px;background:#161B22;'
        f'border:1px solid #30363D;border-left:3px solid {color};'
        f'border-radius:8px;padding:8px 12px;margin-bottom:6px">'
        f'<span style="font-size:1rem">{icon}</span>'
        f'<div style="flex:1">'
        f'<div style="font-size:0.82rem;color:#E6EDF3;font-weight:600">{name}</div>'
        f'<div style="font-size:0.7rem;color:#8B949E">{llm}</div>'
        f'</div>'
        f'<span style="font-size:0.7rem;color:{color};font-weight:600">{status}</span>'
        f'</div>'
    )


def render():
    # ── Page header ────────────────────────────────────────────────
    st.markdown(
        '<h1 style="margin:0 0 2px;font-size:1.6rem;color:#E6EDF3">🌀 Cyclone Mission Control</h1>'
        '<p style="color:#8B949E;margin:0 0 16px;font-size:0.85rem">'
        'Real-time detection · trajectory forecasting · early warning · impact assessment</p>',
        unsafe_allow_html=True,
    )

    # ── Cyclone alert banner ───────────────────────────────────────
    st.markdown(
        '<div style="background:linear-gradient(90deg,#1A0A0A,#2D0D0D);'
        'border:1px solid #E53935;border-radius:10px;padding:10px 16px;'
        'margin-bottom:16px;display:flex;align-items:center;gap:12px">'
        '<span style="font-size:1.4rem">🔴</span>'
        '<div>'
        '<span style="color:#E53935;font-weight:700;font-size:0.95rem">ACTIVE ALERT: </span>'
        '<span style="color:#E6EDF3;font-size:0.9rem">'
        'Extremely Severe Cyclonic Storm <strong>VARUNA</strong> — '
        'Bay of Bengal · Landfall expected near <strong>Visakhapatnam</strong> in ~48h'
        '</span>'
        '</div>'
        '</div>',
        unsafe_allow_html=True,
    )

    # ── 5 KPI cards ───────────────────────────────────────────────
    k1, k2, k3, k4, k5 = st.columns(5)
    _kpi(k1, "🌀", "Cyclone Category", "ESCS-4", "Cat 4 → Landfall", "#E53935")
    _kpi(k2, "💨", "Max Wind Speed",  "130 kt", "↑ from 120 kt",    "#FF6D00")
    _kpi(k3, "🌡️", "Sea Surface Temp","30.2°C", "Warm pool active",  "#FFD600")
    _kpi(k4, "📍", "Landfall ETA",    "T+48h",  "~Visakhapatnam",    "#4FC3F7")
    _kpi(k5, "🛡️", "Alert Level",     "RED",    "7 districts", "#E53935")

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Map + agent pipeline ──────────────────────────────────────
    map_col, pipe_col = st.columns([3, 1], gap="medium")

    with map_col:
        st.markdown(
            '<div style="color:#E6EDF3;font-weight:600;font-size:0.9rem;margin-bottom:6px">'
            '🗺️ 72-Hour Animated Cyclone Track Forecast</div>',
            unsafe_allow_html=True,
        )
        st.markdown(
            '<div style="font-size:0.75rem;color:#8B949E;margin-bottom:8px">'
            'Press <strong style="color:#4FC3F7">▶ Play</strong> to animate track · '
            'drag slider for manual scrub · hover for details</div>',
            unsafe_allow_html=True,
        )
        fig = _build_animated_figure()
        st.plotly_chart(fig, use_container_width=True, key="cyclone_map")

        # Intensity legend
        legend_html = '<div style="display:flex;gap:6px;flex-wrap:wrap;margin-top:4px">'
        for cat, lbl in CAT_LABEL.items():
            legend_html += (
                f'<span style="background:{CAT_COLOR[cat]};color:#000;'
                f'font-size:0.68rem;font-weight:700;padding:2px 8px;border-radius:4px">'
                f'{lbl}</span>'
            )
        legend_html += '</div>'
        st.markdown(legend_html, unsafe_allow_html=True)

    with pipe_col:
        # Agent pipeline status pills
        st.markdown(
            '<div style="color:#E6EDF3;font-weight:600;font-size:0.9rem;margin-bottom:8px">'
            '🤖 Agent Pipeline</div>',
            unsafe_allow_html=True,
        )
        results = st.session_state.get("agent_results", {})

        def _status(key):
            if not results:
                return "PENDING", "#8B949E"
            r = results.get(key, {})
            if r.get("guardrails", {}).get("blocked"):
                return "BLOCKED", "#E53935"
            if r.get("report"):
                return "COMPLETE", "#69F0AE"
            return "PENDING", "#8B949E"

        agents_info = [
            ("weather",   "Weather Analysis",  "watsonx / LLaMA 3"),
            ("detection", "Cyclone Detection", "watsonx / LLaMA 3"),
            ("tracking",  "Track & Predict",   "Gemini Pro"),
            ("intensity", "Intensity Pred.",   "Groq / LLaMA 3"),
            ("impact",    "Impact Assess.",    "Gemini Pro"),
            ("warning",   "Early Warning",     "Groq / LLaMA 3"),
            ("response",  "Disaster Response", "watsonx / LLaMA 3"),
        ]
        phase_colors = ["#4FC3F7", "#4FC3F7", "#FFD600", "#FFD600", "#FF6D00", "#FF6D00", "#E53935"]
        pills_html = ""
        for (key, name, llm), pc in zip(agents_info, phase_colors):
            status, sc = _status(key)
            pills_html += _agent_pill(name, status, sc, llm)

        st.markdown(pills_html, unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)

        # Phase progress
        st.markdown(
            '<div style="color:#8B949E;font-size:0.75rem;margin-bottom:6px;'
            'text-transform:uppercase;letter-spacing:0.05em">Pipeline Phases</div>',
            unsafe_allow_html=True,
        )
        phases = [
            ("Phase 1", "Weather + Detection", "#4FC3F7"),
            ("Phase 2", "Tracking + Intensity", "#FFD600"),
            ("Phase 3", "Impact + Warning", "#FF6D00"),
            ("Phase 4", "Response", "#E53935"),
        ]
        done = sum(1 for k, _, _ in agents_info[:2] if _status(k)[0] == "COMPLETE")
        for i, (ph, desc, pc) in enumerate(phases):
            complete = done > i * 2 if i < 3 else done >= 6
            bar_color = pc if complete else "#30363D"
            st.markdown(
                f'<div style="background:#161B22;border:1px solid #30363D;border-radius:6px;'
                f'padding:6px 10px;margin-bottom:4px;display:flex;justify-content:space-between">'
                f'<span style="font-size:0.75rem;color:#8B949E">'
                f'<span style="color:{bar_color}">●</span> {ph}: {desc}</span>'
                f'</div>',
                unsafe_allow_html=True,
            )

        st.markdown("<br>", unsafe_allow_html=True)

        # Run pipeline button
        if st.button("🚀 Run Full Analysis", use_container_width=True, type="primary"):
            from agents.orchestrator import run_all_agents, ensure_demo_metrics
            ensure_demo_metrics()
            progress_bar = st.progress(0, text="Initializing pipeline…")
            log_area = st.empty()

            def cb(name, done, total):
                progress_bar.progress(done / total, text=f"Running: {name}")
                log_area.markdown(
                    f'<div style="color:#8B949E;font-size:0.75rem">✔ {name}</div>',
                    unsafe_allow_html=True,
                )

            with st.spinner("Running 7-agent pipeline…"):
                st.session_state["agent_results"] = run_all_agents(progress_callback=cb)
            progress_bar.empty()
            log_area.empty()
            st.success("✅ Analysis complete!")
            st.rerun()

    # ── How it works panel ────────────────────────────────────────
    st.markdown("<br>", unsafe_allow_html=True)
    with st.expander("ℹ️ How this dashboard works", expanded=False):
        st.markdown("""
**Architecture:** 7 specialized AI agents run in a 4-phase supervised pipeline, each powered by a different LLM optimized for its task domain.

| Phase | Agents | LLM Provider |
|-------|--------|--------------|
| 1 | Weather Analysis + Cyclone Detection | IBM watsonx (LLaMA 3-70B) |
| 2 | Track & Prediction + Intensity | Google Gemini + Groq LLaMA 3 |
| 3 | Impact Assessment + Early Warning | Google Gemini + Groq LLaMA 3 |
| 4 | Disaster Response | IBM watsonx (LLaMA 3-70B) |

**Memory:** Each agent uses short-term session memory (buffer) + long-term ChromaDB vector store for RAG.

**Guardrails:** 9 categories, 40+ checks (input injection, hallucination, toxicity, PII, jailbreak, cost, HITL, multi-agent loop detection, bias).

**Tools:** MCP-registered tools — `get_weather_data`, `analyze_satellite_image`, `calculate_impact_score`, `generate_alert`.

**Animated Map:** Plotly `frames`-based animation with cyclone eye pulsing, rotating spiral wind bands, and intensity color shifts from green → yellow → orange → red as the storm intensifies.
        """)
