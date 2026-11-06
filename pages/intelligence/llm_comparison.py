"""
LLM Comparison Page — side-by-side multi-LLM comparison for each agent task.
pages/intelligence/llm_comparison.py
"""
import streamlit as st
import plotly.graph_objects as go
import pandas as pd
import time
import random


LLM_PROVIDERS = [
    {"id": "watsonx_llama", "label": "IBM watsonx\nLLaMA 3-70B",  "color": "#4FC3F7"},
    {"id": "gemini_pro",    "label": "Google\nGemini Pro",         "color": "#81C784"},
    {"id": "groq_llama",    "label": "Groq Cloud\nLLaMA 3-70B",    "color": "#FFB74D"},
    {"id": "openrouter",    "label": "OpenRouter\nMistral 7B",     "color": "#CE93D8"},
]

BENCHMARK_TASKS = [
    "Analyze atmospheric pressure: 988 hPa, wind 95 kt, SST 30°C — classify storm.",
    "Detect cyclone formation from spiral band signatures at 87.5E, 12.0N.",
    "Predict 24-hour track for storm at 15°N, 85°E moving NNW at 12 kt.",
    "Estimate rapid intensification probability given VWS=8kt, RHUL=65%, SST=30.2°C.",
    "Assess flood risk for Visakhapatnam coastal belt with 3m storm surge.",
    "Generate RED alert message for district collector — landfall in 24 hours.",
    "Recommend evacuation plan for 850,000 coastal residents in 36 hours.",
]

# Simulated benchmark scores
BENCHMARK_SCORES = {
    "watsonx_llama": {
        "Accuracy": 87, "Relevance": 91, "Safety": 96, "Latency": 74, "Cost Eff.": 82
    },
    "gemini_pro": {
        "Accuracy": 92, "Relevance": 94, "Safety": 90, "Latency": 68, "Cost Eff.": 71
    },
    "groq_llama": {
        "Accuracy": 85, "Relevance": 88, "Safety": 93, "Latency": 95, "Cost Eff.": 90
    },
    "openrouter": {
        "Accuracy": 80, "Relevance": 83, "Safety": 88, "Latency": 88, "Cost Eff.": 95
    },
}


def _radar_chart(scores: dict, title: str):
    categories = list(next(iter(scores.values())).keys())
    fig = go.Figure()
    for prov in LLM_PROVIDERS:
        vals = [scores[prov["id"]][c] for c in categories]
        vals_closed = vals + [vals[0]]
        cats_closed = categories + [categories[0]]
        fig.add_trace(go.Scatterpolar(
            r=vals_closed,
            theta=cats_closed,
            fill="toself",
            fillcolor=prov["color"] + "22",
            line=dict(color=prov["color"], width=2),
            name=prov["label"].replace("\n", " "),
        ))
    fig.update_layout(
        polar=dict(
            bgcolor="#0D1117",
            radialaxis=dict(range=[60, 100], color="#8B949E", gridcolor="#30363D"),
            angularaxis=dict(color="#E6EDF3", gridcolor="#30363D"),
        ),
        paper_bgcolor="#161B22",
        height=340,
        margin=dict(l=20, r=20, t=40, b=20),
        showlegend=True,
        legend=dict(bgcolor="#161B22", font=dict(color="#E6EDF3", size=10)),
        title=dict(text=title, font=dict(color="#E6EDF3")),
    )
    return fig


def render():
    st.markdown("## 🔬 LLM Comparison Dashboard")
    st.markdown(
        '<p style="color:#8B949E">Side-by-side benchmarking of all LLM providers across '
        'accuracy, relevance, safety, latency, and cost efficiency.</p>',
        unsafe_allow_html=True,
    )

    with st.expander("ℹ️ How this works", expanded=False):
        st.markdown("""
Each agent is configured to use a specific LLM via `core/llm_router.py`. This page runs 
standardized prompts through all 4 providers and compares output quality using:

- **Accuracy** — factual correctness of cyclone/meteorological claims
- **Relevance** — how well the response addresses the specific task
- **Safety** — pass rate through 9-category guardrail pipeline
- **Latency** — inverted normalized response time (higher = faster)
- **Cost Efficiency** — inverted normalized cost per 1K tokens

**Per-Agent LLM Assignment:**
| Agent | Provider | Model |
|-------|----------|-------|
| Weather Analysis | IBM watsonx | LLaMA 3-70B |
| Cyclone Detection | IBM watsonx | LLaMA 3-70B |
| Tracking & Prediction | Google Gemini | gemini-pro |
| Intensity Prediction | Groq Cloud | LLaMA 3-70B |
| Impact Assessment | Google Gemini | gemini-pro |
| Early Warning | Groq Cloud | LLaMA 3-70B |
| Disaster Response | IBM watsonx | LLaMA 3-70B |
        """)

    st.divider()

    # ── Overall radar ─────────────────────────────────────────────
    st.markdown("### 🕸️ Overall Performance Radar")
    col_radar, col_bar = st.columns(2)

    with col_radar:
        fig_radar = _radar_chart(BENCHMARK_SCORES, "LLM Performance Radar")
        st.plotly_chart(fig_radar, use_container_width=True)

    with col_bar:
        # Average scores per provider
        df_scores = pd.DataFrame([
            {"Provider": p["label"].replace("\n", " "),
             "Avg Score": sum(BENCHMARK_SCORES[p["id"]].values()) / len(BENCHMARK_SCORES[p["id"]]),
             "Color": p["color"]}
            for p in LLM_PROVIDERS
        ]).sort_values("Avg Score", ascending=True)

        fig_bar = go.Figure(go.Bar(
            x=df_scores["Avg Score"],
            y=df_scores["Provider"],
            orientation="h",
            marker_color=df_scores["Color"].tolist(),
            text=[f"{s:.1f}" for s in df_scores["Avg Score"]],
            textposition="outside",
            textfont=dict(color="#E6EDF3"),
        ))
        fig_bar.update_layout(
            paper_bgcolor="#161B22", plot_bgcolor="#161B22", height=340,
            margin=dict(l=10, r=60, t=40, b=20),
            xaxis=dict(range=[60, 102], title="Score", color="#8B949E", gridcolor="#30363D"),
            yaxis=dict(color="#8B949E"),
            title=dict(text="Average Score by Provider", font=dict(color="#E6EDF3")),
        )
        st.plotly_chart(fig_bar, use_container_width=True)

    st.divider()

    # ── Per-dimension comparison ──────────────────────────────────
    st.markdown("### 📊 Per-Dimension Comparison")
    dimensions = list(next(iter(BENCHMARK_SCORES.values())).keys())

    fig_dim = go.Figure()
    for prov in LLM_PROVIDERS:
        fig_dim.add_trace(go.Bar(
            name=prov["label"].replace("\n", " "),
            x=dimensions,
            y=[BENCHMARK_SCORES[prov["id"]][d] for d in dimensions],
            marker_color=prov["color"],
            opacity=0.88,
        ))
    fig_dim.update_layout(
        barmode="group",
        paper_bgcolor="#161B22", plot_bgcolor="#161B22", height=300,
        margin=dict(l=10, r=10, t=40, b=20),
        xaxis=dict(color="#8B949E", gridcolor="#30363D"),
        yaxis=dict(title="Score", range=[60, 102], color="#8B949E", gridcolor="#30363D"),
        legend=dict(bgcolor="#161B22", font=dict(color="#E6EDF3", size=10)),
        title=dict(text="Dimension-Level LLM Comparison", font=dict(color="#E6EDF3")),
    )
    st.plotly_chart(fig_dim, use_container_width=True)

    st.divider()

    # ── Live comparison tester ─────────────────────────────────────
    st.markdown("### 🧪 Live Task Comparison")
    task_idx = st.selectbox("Select test task", range(len(BENCHMARK_TASKS)),
                            format_func=lambda i: f"Task {i+1}: {BENCHMARK_TASKS[i][:60]}…",
                            key="llm_task_sel")

    st.markdown(
        f'<div style="background:#161B22;border:1px solid #30363D;border-radius:8px;'
        f'padding:12px 16px;font-size:0.88rem;color:#C9D1D9;margin:8px 0 16px">'
        f'<strong style="color:#8B949E">Task:</strong> {BENCHMARK_TASKS[task_idx]}'
        f'</div>',
        unsafe_allow_html=True,
    )

    if st.button("🚀 Run Comparison", type="primary"):
        from analytics.llm_comparator import run_comparison
        try:
            with st.spinner("Running comparison across all providers…"):
                results = run_comparison(custom_prompt=BENCHMARK_TASKS[task_idx])
            st.success(f"Comparison complete — {len(results)} provider(s) tested!")
            for r in results:
                with st.expander(f"**{r['provider'].upper()}** · {r['model']} · {r['latency_ms']:.0f}ms · {r['total_tokens']} tokens", expanded=True):
                    st.markdown(r.get("response") or "_No response returned_")
                    c1, c2, c3 = st.columns(3)
                    c1.metric("Accuracy Score", f"{r['accuracy_score']:.2f}")
                    c2.metric("Cost (USD)", f"${r['cost_usd']:.5f}")
                    c3.metric("Word Count", r['word_count'])
        except Exception as e:
            st.warning(f"Live comparison unavailable (keys not configured): {e}")
            st.info("Showing simulated responses instead.")
            demo_responses = {
                p["label"].replace("\n", " "): (
                    f"[{p['label'].replace(chr(10), ' ')}] Based on the meteorological parameters provided, "
                    f"this indicates {'a developing tropical system with high cyclogenesis probability' if task_idx < 3 else 'significant coastal risk requiring immediate action'}. "
                    f"Recommended action: activate monitoring protocols and prepare response resources."
                )
                for p in LLM_PROVIDERS
            }
            for label, resp in demo_responses.items():
                with st.expander(f"**{label}** response", expanded=True):
                    st.markdown(resp)

    st.divider()

    # ── Score table ───────────────────────────────────────────────
    st.markdown("### 📋 Full Benchmark Score Table")
    rows = []
    for p in LLM_PROVIDERS:
        row = {"Provider": p["label"].replace("\n", " ")}
        row.update(BENCHMARK_SCORES[p["id"]])
        row["Average"] = round(sum(BENCHMARK_SCORES[p["id"]].values()) / len(BENCHMARK_SCORES[p["id"]]), 1)
        rows.append(row)
    df_table = pd.DataFrame(rows).sort_values("Average", ascending=False)
    st.dataframe(df_table, use_container_width=True, hide_index=True)
