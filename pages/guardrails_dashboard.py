"""
Guardrails Dashboard — shows all 9 guardrail categories, real-time events, and status.
Rendered as a function called from app.py.
"""
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from utils import guardrails as gr
from utils.metrics_tracker import get_guardrail_events


CATEGORY_META = {
    "Input":       {"icon": "🔍", "color": "#4FC3F7", "checks": 5},
    "Output":      {"icon": "📤", "color": "#81C784", "checks": 5},
    "Tool":        {"icon": "🔧", "color": "#FFB74D", "checks": 3},
    "Data":        {"icon": "🗄️", "color": "#CE93D8", "checks": 2},
    "Security":    {"icon": "🔒", "color": "#E84545", "checks": 4},
    "Operational": {"icon": "⚙️", "color": "#F48FB1", "checks": 4},
    "HITL":        {"icon": "👤", "color": "#80DEEA", "checks": 2},
    "MultiAgent":  {"icon": "🤝", "color": "#FFCC80", "checks": 3},
    "Ethical":     {"icon": "⚖️", "color": "#A5D6A7", "checks": 4},
}


def render():
    st.markdown("## 🛡️ Guardrails Dashboard")
    st.markdown('<p style="color:#8B949E">Real-time monitoring of all 9 guardrail categories with 40+ safety checks across the agent pipeline.</p>', unsafe_allow_html=True)

    events = get_guardrail_events()
    if not events:
        # Seed a demo pipeline run
        _run_demo_checks()
        events = get_guardrail_events()

    df = pd.DataFrame(events)

    # ── KPI row ──────────────────────────────────────────────────
    total     = len(df)
    triggered = df["triggered"].sum() if "triggered" in df.columns else 0
    blocked   = df[df["severity"] == "critical"]["triggered"].sum() if total else 0
    pass_rate = round((total - triggered) / max(total, 1) * 100, 1)

    c1, c2, c3, c4, c5 = st.columns(5)
    _kpi(c1, "Total Checks",    str(total),          "#E6EDF3")
    _kpi(c2, "Passed",          str(total-triggered), "#69F0AE")
    _kpi(c3, "Flagged",         str(triggered),       "#FFD740" if triggered else "#69F0AE")
    _kpi(c4, "Critical Blocks", str(int(blocked)),    "#FF8A80" if blocked else "#69F0AE")
    _kpi(c5, "Pass Rate",       f"{pass_rate}%",      "#69F0AE" if pass_rate >= 90 else "#FFD740")

    st.divider()

    # ── Category overview ────────────────────────────────────────
    st.markdown("### 🗂️ Guardrail Categories Overview")

    cat_cols = st.columns(3)
    for idx, (cat, meta) in enumerate(CATEGORY_META.items()):
        cat_events = df[df["category"] == cat] if "category" in df.columns else pd.DataFrame()
        cat_total  = len(cat_events)
        cat_fail   = cat_events["triggered"].sum() if cat_total else 0
        status     = "✅ PASS" if cat_fail == 0 else f"⚠️ {int(cat_fail)} flagged"
        status_col = "#69F0AE" if cat_fail == 0 else "#FFD740"

        with cat_cols[idx % 3]:
            st.markdown(
                f'<div style="background:#161B22;border:1px solid #30363D;border-left:4px solid {meta["color"]};'
                f'border-radius:8px;padding:14px 16px;margin-bottom:10px">'
                f'<div style="font-size:1.3rem">{meta["icon"]} <strong style="color:#E6EDF3">{cat}</strong></div>'
                f'<div style="font-size:0.8rem;color:#8B949E;margin:4px 0">{meta["checks"]} checks registered</div>'
                f'<div style="font-size:0.85rem;color:{status_col};font-weight:600">{status}</div>'
                f'</div>',
                unsafe_allow_html=True,
            )

    st.divider()

    # ── Charts row ───────────────────────────────────────────────
    col_pie, col_bar, col_sev = st.columns(3)

    with col_pie:
        st.markdown("#### Pass / Fail by Category")
        if "category" in df.columns:
            cat_counts = df.groupby(["category","triggered"]).size().reset_index(name="n")
            fig = px.sunburst(cat_counts, path=["category","triggered"], values="n",
                              color="triggered",
                              color_discrete_map={True:"#E84545", False:"#43A047"})
            fig.update_layout(paper_bgcolor="#161B22", margin=dict(l=0,r=0,t=10,b=0),
                              height=280, font=dict(color="#E6EDF3"))
            st.plotly_chart(fig, use_container_width=True)

    with col_bar:
        st.markdown("#### Checks per Category")
        if "category" in df.columns:
            g = df.groupby("category").agg(
                total=("triggered","count"),
                flagged=("triggered","sum")
            ).reset_index()
            g["passed"] = g["total"] - g["flagged"]
            fig2 = go.Figure()
            fig2.add_trace(go.Bar(x=g["category"], y=g["passed"],  name="Passed",  marker_color="#43A047"))
            fig2.add_trace(go.Bar(x=g["category"], y=g["flagged"], name="Flagged", marker_color="#E84545"))
            fig2.update_layout(barmode="stack", paper_bgcolor="#161B22",
                               plot_bgcolor="#161B22", height=280,
                               margin=dict(l=0,r=0,t=10,b=0),
                               xaxis=dict(color="#8B949E", tickangle=30, tickfont=dict(size=9)),
                               yaxis=dict(color="#8B949E", gridcolor="#30363D"),
                               legend=dict(bgcolor="#161B22", font=dict(color="#E6EDF3")))
            st.plotly_chart(fig2, use_container_width=True)

    with col_sev:
        st.markdown("#### Severity Distribution")
        if "severity" in df.columns and triggered > 0:
            sev_df = df[df["triggered"]].groupby("severity").size().reset_index(name="n")
            colors = {"low":"#43A047","medium":"#FFD600","high":"#FF6F00","critical":"#E53935"}
            fig3 = go.Figure(go.Pie(
                labels=sev_df["severity"], values=sev_df["n"],
                marker_colors=[colors.get(s,"#8B949E") for s in sev_df["severity"]],
                hole=0.5,
            ))
            fig3.update_layout(paper_bgcolor="#161B22", height=280,
                               margin=dict(l=0,r=0,t=10,b=0),
                               font=dict(color="#E6EDF3"),
                               legend=dict(bgcolor="#161B22"))
            st.plotly_chart(fig3, use_container_width=True)
        else:
            st.markdown('<div style="text-align:center;color:#69F0AE;padding:40px;font-size:2rem">✅<br><span style="font-size:1rem">No flags raised</span></div>', unsafe_allow_html=True)

    st.divider()

    # ── Live event log ───────────────────────────────────────────
    st.markdown("### 📋 Guardrail Event Log")

    col_filter1, col_filter2 = st.columns(2)
    with col_filter1:
        cat_filter = st.multiselect("Filter by Category", list(CATEGORY_META.keys()),
                                    default=[], key="gr_cat_filter")
    with col_filter2:
        show_flags_only = st.checkbox("Show flagged only", value=False, key="gr_flags_only")

    disp = df.copy()
    if cat_filter:
        disp = disp[disp["category"].isin(cat_filter)]
    if show_flags_only:
        disp = disp[disp["triggered"] == True]

    if not disp.empty:
        disp["Status"] = disp["triggered"].map({True:"🔴 Flagged", False:"✅ Passed"})
        disp_show = disp[["ts","category","check","Status","severity","agent","detail"]].rename(columns={
            "ts":"Timestamp","category":"Category","check":"Check",
            "severity":"Severity","agent":"Agent","detail":"Detail"
        })
        st.dataframe(disp_show, use_container_width=True, hide_index=True, height=300)
    else:
        st.info("No events match the current filter.")

    st.divider()

    # ── Guardrail categories explanation ────────────────────────
    st.markdown("### 📖 Guardrail Categories Reference")
    guardrail_info = [
        ("🔍 Input",       "Prompt injection, malicious input, PII, inappropriate content, input validation"),
        ("📤 Output",      "Hallucination, factual accuracy, toxicity, sensitive information, format validation"),
        ("🔧 Tool",        "Tool permissions, function-call validation, tool call count limits"),
        ("🗄️ Data",        "Data privacy, role-based access, PII masking, unauthorised data retrieval prevention"),
        ("🔒 Security",    "Jailbreak detection, SQL injection, credential exposure, cross-agent trust"),
        ("⚙️ Operational", "Token budget, cost budget, agent iteration limits, API rate limiting"),
        ("👤 HITL",        "Human approval for critical actions, confidence-based manual review escalation"),
        ("🤝 Multi-Agent", "Loop detection, handoff validity, task assignment validation"),
        ("⚖️ Ethical",     "Bias detection, fairness validation, regulatory compliance, audit trail"),
    ]
    cols = st.columns(3)
    for i, (title, desc) in enumerate(guardrail_info):
        with cols[i % 3]:
            st.markdown(
                f'<div style="background:#161B22;border:1px solid #30363D;border-radius:8px;padding:12px 14px;margin-bottom:8px">'
                f'<strong style="color:#E6EDF3">{title}</strong>'
                f'<p style="font-size:0.78rem;color:#8B949E;margin:4px 0 0">{desc}</p>'
                f'</div>',
                unsafe_allow_html=True,
            )


def _run_demo_checks():
    """Run a quick guardrail pipeline to populate the event log."""
    demo_text = (
        "Extremely Severe Cyclonic Storm VARUNA is approaching the Andhra Pradesh coast. "
        "Sea surface temperature is 29.8°C. NDMA evacuation protocols should be activated. "
        "All coastal districts are advised to prepare."
    )
    demo_prompt = "Analyze meteorological data for cyclone detection."
    agents = [
        "Weather Data Analysis Agent", "Cyclone Detection Agent",
        "Cyclone Tracking & Prediction Agent", "Cyclone Intensity Prediction Agent",
        "Impact Assessment Agent", "Early Warning & Alert Agent",
        "Disaster Response Recommendation Agent",
    ]
    for ag in agents:
        gr.run_full_pipeline(
            prompt=demo_prompt, output=demo_text,
            agent_name=ag, tokens_used=350, cost=0.0003, confidence=0.91
        )


def _kpi(col, label, value, color):
    with col:
        st.markdown(
            f'<div style="background:#161B22;border:1px solid #30363D;border-radius:10px;'
            f'padding:14px 10px;text-align:center;margin-bottom:8px">'
            f'<div style="font-size:1.5rem;font-weight:700;color:{color}">{value}</div>'
            f'<div style="font-size:0.75rem;color:#8B949E;text-transform:uppercase;letter-spacing:0.06em">{label}</div>'
            f'</div>',
            unsafe_allow_html=True,
        )
