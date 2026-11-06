"""
Shared helpers for all agent detail pages.
"""
import streamlit as st
import plotly.graph_objects as go


PROVIDER_BADGE = {
    "watsonx": ("#4FC3F7", "IBM watsonx"),
    "gemini":  ("#81C784", "Google Gemini"),
    "groq":    ("#FFB74D", "Groq Cloud"),
    "demo":    ("#8B949E", "Demo Mode"),
}


def page_header(agent_name: str, icon: str, tagline: str, llm: str, provider: str):
    color, label = PROVIDER_BADGE.get(provider, ("#8B949E", provider))
    st.markdown(
        f'<div style="margin-bottom:16px">'
        f'<h1 style="margin:0;font-size:1.5rem;color:#E6EDF3">{icon} {agent_name}</h1>'
        f'<p style="color:#8B949E;margin:4px 0 10px;font-size:0.85rem">{tagline}</p>'
        f'<span style="background:#161B22;border:1px solid {color};border-radius:6px;'
        f'padding:4px 12px;font-size:0.78rem;color:{color};font-weight:600">'
        f'🤖 {label} · {llm}</span>'
        f'</div>',
        unsafe_allow_html=True,
    )


def how_it_works_panel(llm: str, tools: list[str], memory: str, guardrails: str,
                        react_steps: int, token_budget: int):
    with st.expander("ℹ️ How this agent works", expanded=False):
        c1, c2, c3 = st.columns(3)
        with c1:
            st.markdown(f"**🧠 LLM**  \n`{llm}`")
            st.markdown(f"**🔄 ReAct Steps**  \nUp to {react_steps}")
        with c2:
            st.markdown(f"**🗄️ Memory**  \n{memory}")
            st.markdown(f"**💰 Token Budget**  \n{token_budget:,}")
        with c3:
            st.markdown(f"**🛡️ Guardrails**  \n{guardrails}")
            st.markdown(f"**🔧 Tools**  \n{', '.join(tools)}")


def result_report_card(result: dict):
    """Display the agent's output report."""
    report = result.get("report", "")
    if not report:
        st.info("No report yet — run the pipeline from the dashboard.")
        return

    conf  = result.get("confidence", 0.88)
    react = result.get("react_steps", 0)
    tools = result.get("tool_calls_made", 0)
    gr    = result.get("guardrails", {})
    blocked = gr.get("blocked", False)

    # Status bar
    status_color = "#E53935" if blocked else "#69F0AE"
    status_text  = "🔴 BLOCKED" if blocked else "✅ PASSED"
    col1, col2, col3, col4 = st.columns(4)
    for col, lbl, val, c in [
        (col1, "Status",       status_text,        status_color),
        (col2, "Confidence",   f"{conf:.0%}",       "#4FC3F7"),
        (col3, "ReAct Steps",  str(react),          "#E6EDF3"),
        (col4, "Tool Calls",   str(tools),          "#FFD600"),
    ]:
        with col:
            st.markdown(
                f'<div style="background:#161B22;border:1px solid #30363D;border-radius:8px;'
                f'padding:10px;text-align:center">'
                f'<div style="font-weight:700;color:{c};font-size:1.1rem">{val}</div>'
                f'<div style="font-size:0.7rem;color:#8B949E;text-transform:uppercase">{lbl}</div>'
                f'</div>',
                unsafe_allow_html=True,
            )

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown(
        f'<div style="background:#161B22;border:1px solid #30363D;border-radius:10px;'
        f'padding:16px 20px;white-space:pre-wrap;font-size:0.85rem;'
        f'color:#E6EDF3;line-height:1.65;max-height:340px;overflow-y:auto">'
        f'{report.replace(chr(60), "&lt;").replace(chr(62), "&gt;")}'
        f'</div>',
        unsafe_allow_html=True,
    )


def run_agent_button(agent_key: str, button_label: str = "▶ Run This Agent"):
    if st.button(button_label, type="primary"):
        from agents.orchestrator import run_single_agent, ensure_demo_metrics
        ensure_demo_metrics()
        with st.spinner("Running agent…"):
            result = run_single_agent(agent_key)
        if "agent_results" not in st.session_state:
            st.session_state["agent_results"] = {}
        st.session_state["agent_results"][agent_key] = result
        st.rerun()
