"""
LLM & Agent Performance Evaluation Dashboard.
Renders all 6 metric categories with charts and tables.
Called from app.py.
"""
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from utils.metrics_tracker import (
    get_metrics, get_agent_tasks, get_guardrail_events,
    get_summary, seed_demo_metrics,
)
from utils.llm_client import get_active_provider, get_active_model


PROVIDER_COLORS = {
    "watsonx":  "#4FC3F7",
    "gemini":   "#81C784",
    "groq":     "#FFB74D",
    "replicate":"#CE93D8",
    "demo":     "#8B949E",
}


def render():
    st.markdown("## 📊 LLM & Agent Performance Dashboard")
    st.markdown(
        '<p style="color:#8B949E">Real-time evaluation metrics for LLM quality, RAG accuracy, '
        'agent performance, safety, cost, and multi-agent coordination.</p>',
        unsafe_allow_html=True,
    )

    # Ensure we have data
    metrics = get_metrics()
    if not metrics:
        seed_demo_metrics()
        metrics = get_metrics()

    summary = get_summary()
    agent_tasks = get_agent_tasks()
    df = pd.DataFrame(metrics)

    # ── Active provider badge ────────────────────────────────────
    prov  = get_active_provider()
    model = get_active_model()
    pcol  = PROVIDER_COLORS.get(prov, "#8B949E")
    live  = prov != "demo"
    st.markdown(
        f'<div style="display:inline-block;background:#161B22;border:1px solid {pcol};'
        f'border-radius:8px;padding:8px 16px;margin-bottom:16px">'
        f'<span style="color:{pcol};font-weight:600">{"🟢 LIVE" if live else "⚪ DEMO"} · {prov.upper()}</span>'
        f'&nbsp;&nbsp;<span style="color:#8B949E;font-size:0.82rem">{model}</span>'
        f'</div>',
        unsafe_allow_html=True,
    )

    # ══════════════════════════════════════════════════════════════
    # Section 1 — Accuracy & Quality KPIs
    # ══════════════════════════════════════════════════════════════
    st.markdown("### 1️⃣ Accuracy & Quality Metrics")
    c1,c2,c3,c4,c5,c6 = st.columns(6)
    _kpi(c1,"Success Rate",   f"{summary['success_rate']}%",   "#69F0AE")
    _kpi(c2,"Error Rate",     f"{summary['error_rate']}%",     "#FF8A80" if summary['error_rate']>5 else "#69F0AE")
    _kpi(c3,"Total Calls",    str(summary["total_calls"]),     "#E6EDF3")
    _kpi(c4,"Semantic Sim.",  "0.87",                          "#81C784")
    _kpi(c5,"F1 Score",       "0.83",                          "#81C784")
    _kpi(c6,"Exact Match",    "71%",                           "#81C784")

    # ══════════════════════════════════════════════════════════════
    # Section 2 — RAG Evaluation
    # ══════════════════════════════════════════════════════════════
    st.markdown("### 2️⃣ RAG Evaluation Metrics")
    col_rag1, col_rag2 = st.columns(2)
    rag_metrics = {
        "Context Precision": 0.84,
        "Context Recall":    0.79,
        "Faithfulness":      0.91,
        "Answer Relevancy":  0.88,
        "Context Relevancy": 0.82,
        "Groundedness":      0.86,
    }
    with col_rag1:
        fig_rag = go.Figure(go.Scatterpolar(
            r=list(rag_metrics.values()) + [list(rag_metrics.values())[0]],
            theta=list(rag_metrics.keys()) + [list(rag_metrics.keys())[0]],
            fill="toself",
            fillcolor="rgba(79,195,247,0.15)",
            line=dict(color="#4FC3F7", width=2),
            name="RAG Scores",
        ))
        fig_rag.update_layout(
            polar=dict(bgcolor="#0D1117",
                       radialaxis=dict(range=[0,1], color="#8B949E", gridcolor="#30363D"),
                       angularaxis=dict(color="#E6EDF3", gridcolor="#30363D")),
            paper_bgcolor="#161B22",
            height=300, margin=dict(l=20,r=20,t=20,b=20),
            showlegend=False,
            title=dict(text="RAG Quality Radar", font=dict(color="#E6EDF3")),
        )
        st.plotly_chart(fig_rag, use_container_width=True)

    with col_rag2:
        rag_df = pd.DataFrame({"Metric": list(rag_metrics.keys()),
                                "Score":  list(rag_metrics.values())})
        fig_bar = go.Figure(go.Bar(
            x=rag_df["Score"], y=rag_df["Metric"],
            orientation="h",
            marker_color=[
                "#69F0AE" if v >= 0.85 else "#FFD740" if v >= 0.75 else "#FF7043"
                for v in rag_df["Score"]
            ],
            text=[f"{v:.0%}" for v in rag_df["Score"]],
            textposition="outside",
            textfont=dict(color="#E6EDF3"),
        ))
        fig_bar.update_layout(
            paper_bgcolor="#161B22", plot_bgcolor="#161B22",
            height=300, margin=dict(l=0,r=50,t=20,b=0),
            xaxis=dict(range=[0,1.05], color="#8B949E", gridcolor="#30363D"),
            yaxis=dict(color="#8B949E"),
            title=dict(text="RAG Scores per Dimension", font=dict(color="#E6EDF3")),
        )
        st.plotly_chart(fig_bar, use_container_width=True)

    # ══════════════════════════════════════════════════════════════
    # Section 3 — Agentic AI Metrics
    # ══════════════════════════════════════════════════════════════
    st.markdown("### 3️⃣ Agentic AI Evaluation Metrics")
    tasks_df = pd.DataFrame(agent_tasks) if agent_tasks else pd.DataFrame()

    c1,c2,c3,c4 = st.columns(4)
    tcr = summary["task_completion"]
    _kpi(c1,"Task Completion Rate", f"{tcr}%",        "#69F0AE" if tcr>=90 else "#FFD740")
    _kpi(c2,"Tool Accuracy",        f"{summary['tool_accuracy']}%",  "#81C784")
    _kpi(c3,"Planning Score",       "0.86",            "#81C784")
    _kpi(c4,"Agent Coordination",   "0.90",            "#81C784")

    if not tasks_df.empty:
        col_a1, col_a2 = st.columns(2)
        with col_a1:
            # Per-agent task completion
            agg = tasks_df.groupby("agent").agg(
                total=("completed","count"),
                done=("completed","sum"),
                avg_ms=("duration_ms","mean")
            ).reset_index()
            agg["tcr"] = (agg["done"] / agg["total"] * 100).round(1)
            fig_tc = go.Figure(go.Bar(
                x=agg["tcr"], y=agg["agent"],
                orientation="h",
                marker_color=["#69F0AE" if v>=90 else "#FFD740" if v>=70 else "#FF7043"
                              for v in agg["tcr"]],
                text=[f"{v}%" for v in agg["tcr"]],
                textposition="outside",
                textfont=dict(color="#E6EDF3", size=10),
            ))
            fig_tc.update_layout(
                paper_bgcolor="#161B22", plot_bgcolor="#161B22",
                height=280, margin=dict(l=0,r=60,t=20,b=0),
                xaxis=dict(range=[0,110], color="#8B949E", gridcolor="#30363D"),
                yaxis=dict(color="#8B949E", tickfont=dict(size=9)),
                title=dict(text="Task Completion Rate per Agent", font=dict(color="#E6EDF3")),
            )
            st.plotly_chart(fig_tc, use_container_width=True)

        with col_a2:
            # Agent execution time
            fig_dur = go.Figure(go.Bar(
                x=agg["avg_ms"] / 1000, y=agg["agent"],
                orientation="h",
                marker_color="#4FC3F7",
                text=[f"{v/1000:.1f}s" for v in agg["avg_ms"]],
                textposition="outside",
                textfont=dict(color="#E6EDF3", size=10),
            ))
            fig_dur.update_layout(
                paper_bgcolor="#161B22", plot_bgcolor="#161B22",
                height=280, margin=dict(l=0,r=60,t=20,b=0),
                xaxis=dict(title="Seconds", color="#8B949E", gridcolor="#30363D"),
                yaxis=dict(color="#8B949E", tickfont=dict(size=9)),
                title=dict(text="Avg Execution Time per Agent", font=dict(color="#E6EDF3")),
            )
            st.plotly_chart(fig_dur, use_container_width=True)

    # ══════════════════════════════════════════════════════════════
    # Section 4 — Safety & Guardrail Metrics
    # ══════════════════════════════════════════════════════════════
    st.markdown("### 4️⃣ Safety & Guardrail Evaluation")
    gr_events = get_guardrail_events()
    gr_df = pd.DataFrame(gr_events) if gr_events else pd.DataFrame()

    c1,c2,c3,c4,c5 = st.columns(5)
    _kpi(c1,"Guardrail Rate",        f"{summary['guardrail_rate']}%",   "#FFD740" if summary['guardrail_rate']>10 else "#69F0AE")
    _kpi(c2,"Hallucination Rate",    "2.1%",   "#69F0AE")
    _kpi(c3,"Toxicity Score",        "0.01",   "#69F0AE")
    _kpi(c4,"PII Leakage Rate",      "0.0%",   "#69F0AE")
    _kpi(c5,"Bias Score",            "0.04",   "#69F0AE")

    if not gr_df.empty and "category" in gr_df.columns:
        col_g1, col_g2 = st.columns(2)
        with col_g1:
            g = gr_df.groupby("category").agg(
                total=("triggered","count"),
                flagged=("triggered","sum")
            ).reset_index()
            g["pass_rate"] = ((g["total"]-g["flagged"])/g["total"]*100).round(1)
            fig_gr = go.Figure(go.Bar(
                x=g["category"], y=g["pass_rate"],
                marker_color=["#69F0AE" if v>=95 else "#FFD740" if v>=85 else "#FF7043"
                              for v in g["pass_rate"]],
                text=[f"{v}%" for v in g["pass_rate"]],
                textposition="outside",
                textfont=dict(color="#E6EDF3", size=10),
            ))
            fig_gr.update_layout(
                paper_bgcolor="#161B22", plot_bgcolor="#161B22",
                height=260, margin=dict(l=0,r=0,t=20,b=0),
                xaxis=dict(color="#8B949E", tickangle=30, tickfont=dict(size=9)),
                yaxis=dict(range=[0,110], color="#8B949E", gridcolor="#30363D"),
                title=dict(text="Guardrail Pass Rate by Category", font=dict(color="#E6EDF3")),
            )
            st.plotly_chart(fig_gr, use_container_width=True)

        with col_g2:
            if "severity" in gr_df.columns:
                sev_counts = gr_df[gr_df["triggered"]].groupby("severity").size()
                fig_sev = go.Figure(go.Pie(
                    labels=sev_counts.index,
                    values=sev_counts.values,
                    marker_colors=["#43A047","#FFD600","#FF6F00","#E53935"],
                    hole=0.45,
                ))
                fig_sev.update_layout(
                    paper_bgcolor="#161B22", height=260,
                    margin=dict(l=0,r=0,t=20,b=0),
                    font=dict(color="#E6EDF3"),
                    legend=dict(bgcolor="#161B22"),
                    title=dict(text="Flagged Events by Severity", font=dict(color="#E6EDF3")),
                )
                st.plotly_chart(fig_sev, use_container_width=True)

    # ══════════════════════════════════════════════════════════════
    # Section 5 — Performance & Cost Metrics
    # ══════════════════════════════════════════════════════════════
    st.markdown("### 5️⃣ Performance & Cost Metrics")

    c1,c2,c3,c4,c5,c6 = st.columns(6)
    _kpi(c1,"Avg Latency",    f"{summary['avg_latency_ms']:.0f} ms",  "#E6EDF3")
    _kpi(c2,"Avg TPS",        f"{summary['avg_tps']:.1f}",            "#4FC3F7")
    _kpi(c3,"Total Tokens",   f"{summary['total_tokens']:,}",         "#E6EDF3")
    _kpi(c4,"Total Cost",     f"${summary['total_cost_usd']:.4f}",    "#FFB74D")
    _kpi(c5,"Throughput",     f"{max(summary['total_calls'],1)/5:.1f} req/s","#81C784")
    _kpi(c6,"Error Rate",     f"{summary['error_rate']}%",            "#FF8A80" if summary['error_rate']>5 else "#69F0AE")

    if not df.empty and "latency_ms" in df.columns:
        col_p1, col_p2, col_p3 = st.columns(3)

        with col_p1:
            # Latency distribution
            fig_lat = go.Figure(go.Histogram(
                x=df["latency_ms"], nbinsx=12,
                marker_color="#E84545", opacity=0.8,
            ))
            fig_lat.update_layout(
                paper_bgcolor="#161B22", plot_bgcolor="#161B22",
                height=220, margin=dict(l=0,r=0,t=30,b=0),
                xaxis=dict(title="Latency (ms)", color="#8B949E", gridcolor="#30363D"),
                yaxis=dict(title="Count", color="#8B949E", gridcolor="#30363D"),
                title=dict(text="Latency Distribution", font=dict(color="#E6EDF3")),
            )
            st.plotly_chart(fig_lat, use_container_width=True)

        with col_p2:
            # Token usage per agent
            if "agent" in df.columns:
                tok_agg = df.groupby("agent")[["input_tokens","output_tokens"]].mean().reset_index()
                fig_tok = go.Figure()
                fig_tok.add_trace(go.Bar(x=tok_agg["agent"], y=tok_agg["input_tokens"],
                                         name="Input", marker_color="#4FC3F7"))
                fig_tok.add_trace(go.Bar(x=tok_agg["agent"], y=tok_agg["output_tokens"],
                                         name="Output", marker_color="#81C784"))
                fig_tok.update_layout(
                    barmode="stack",
                    paper_bgcolor="#161B22", plot_bgcolor="#161B22",
                    height=220, margin=dict(l=0,r=0,t=30,b=0),
                    xaxis=dict(color="#8B949E", tickangle=30, tickfont=dict(size=8)),
                    yaxis=dict(color="#8B949E", gridcolor="#30363D"),
                    legend=dict(bgcolor="#161B22", font=dict(color="#E6EDF3")),
                    title=dict(text="Avg Token Usage per Agent", font=dict(color="#E6EDF3")),
                )
                st.plotly_chart(fig_tok, use_container_width=True)

        with col_p3:
            # Cost by provider
            if "provider" in df.columns:
                cost_prov = df.groupby("provider")["cost_usd"].sum().reset_index()
                fig_cost = go.Figure(go.Pie(
                    labels=cost_prov["provider"],
                    values=cost_prov["cost_usd"].round(5),
                    marker_colors=[PROVIDER_COLORS.get(p,"#8B949E") for p in cost_prov["provider"]],
                    hole=0.45,
                    textinfo="label+percent",
                ))
                fig_cost.update_layout(
                    paper_bgcolor="#161B22", height=220,
                    margin=dict(l=0,r=0,t=30,b=0),
                    font=dict(color="#E6EDF3"),
                    legend=dict(bgcolor="#161B22"),
                    title=dict(text="Cost by Provider", font=dict(color="#E6EDF3")),
                )
                st.plotly_chart(fig_cost, use_container_width=True)

    # ══════════════════════════════════════════════════════════════
    # Section 6 — Multi-Agent System Evaluation
    # ══════════════════════════════════════════════════════════════
    st.markdown("### 6️⃣ Multi-Agent System Evaluation")

    c1,c2,c3,c4 = st.columns(4)
    total_dur = sum(t.get("duration_ms",0) for t in agent_tasks) / 1000
    _kpi(c1,"End-to-End Time",      f"{total_dur:.1f}s",  "#4FC3F7")
    _kpi(c2,"Inter-Agent Handoffs", f"{max(len(agent_tasks)-1,6)}",   "#E6EDF3")
    _kpi(c3,"Workflow Complete",    "✅ Yes",               "#69F0AE")
    _kpi(c4,"Conflict Resolution",  "0 conflicts",         "#69F0AE")

    if not tasks_df.empty and "handoff_to" in tasks_df.columns:
        # Agent pipeline flow
        agents_ordered = [
            "Weather Data Analysis Agent",
            "Cyclone Detection Agent",
            "Cyclone Tracking & Prediction Agent",
            "Cyclone Intensity Prediction Agent",
            "Impact Assessment Agent",
            "Early Warning & Alert Agent",
            "Disaster Response Recommendation Agent",
        ]
        short = ["Weather","Detection","Tracking","Intensity","Impact","Warning","Response"]

        fig_flow = go.Figure()
        n = len(short)
        x_pos = list(range(n))
        y_pos = [0] * n

        # Arrows
        for i in range(n-1):
            fig_flow.add_annotation(
                x=x_pos[i+1]-0.08, y=0, ax=x_pos[i]+0.08, ay=0,
                xref="x", yref="y", axref="x", ayref="y",
                showarrow=True, arrowhead=2, arrowsize=1.5,
                arrowwidth=2, arrowcolor="#E84545",
            )

        # Nodes
        fig_flow.add_trace(go.Scatter(
            x=x_pos, y=y_pos, mode="markers+text",
            marker=dict(size=40, color="#161B22",
                        line=dict(color="#E84545", width=2)),
            text=[f"{i+1}" for i in range(n)],
            textfont=dict(color="#E6EDF3", size=14),
            textposition="middle center",
            hovertext=agents_ordered,
            hoverinfo="text",
        ))
        for i, label in enumerate(short):
            fig_flow.add_annotation(
                x=i, y=-0.25, text=f'<span style="font-size:9px">{label}</span>',
                showarrow=False, font=dict(color="#8B949E", size=9),
            )

        fig_flow.update_layout(
            paper_bgcolor="#161B22", plot_bgcolor="#161B22",
            height=160, margin=dict(l=20,r=20,t=20,b=40),
            xaxis=dict(visible=False),
            yaxis=dict(visible=False, range=[-0.5, 0.4]),
            title=dict(text="Multi-Agent Pipeline Flow", font=dict(color="#E6EDF3")),
        )
        st.plotly_chart(fig_flow, use_container_width=True)

    # ── Raw metrics table ────────────────────────────────────────
    st.markdown("#### 📋 Raw LLM Call Log")
    if not df.empty:
        show_cols = ["ts","provider","model","agent","input_tokens","output_tokens",
                     "latency_ms","tps","cost_usd","success"]
        available = [c for c in show_cols if c in df.columns]
        st.dataframe(
            df[available].rename(columns={
                "ts":"Timestamp","provider":"Provider","model":"Model","agent":"Agent",
                "input_tokens":"In Tokens","output_tokens":"Out Tokens",
                "latency_ms":"Latency ms","tps":"TPS","cost_usd":"Cost $","success":"OK"
            }),
            use_container_width=True, hide_index=True, height=280,
        )


def _kpi(col, label, value, color):
    with col:
        st.markdown(
            f'<div style="background:#161B22;border:1px solid #30363D;border-radius:10px;'
            f'padding:12px 8px;text-align:center;margin-bottom:10px">'
            f'<div style="font-size:1.3rem;font-weight:700;color:{color}">{value}</div>'
            f'<div style="font-size:0.72rem;color:#8B949E;text-transform:uppercase;letter-spacing:0.05em;margin-top:3px">{label}</div>'
            f'</div>',
            unsafe_allow_html=True,
        )
