"""
Cyclone Detection & Early Warning System
IBM Bob + IBM Granite LLM + IBM Cloud

app.py — clean router (~80 lines). All pages live in pages/subfolders.
"""
import streamlit as st

st.set_page_config(
    page_title="Cyclone Detection & Early Warning",
    page_icon="🌀",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Custom CSS injection ────────────────────────────────────────────────────
st.markdown("""
<style>
  [data-testid="stSidebar"] { background: #0D1117; border-right: 1px solid #21262D; }
  [data-testid="stSidebar"] .stRadio label { font-size: 0.85rem; }
  .block-container { padding-top: 1.2rem; padding-bottom: 1rem; }
  h1, h2, h3 { color: #E6EDF3 !important; }
  .stMetric { background: #161B22; border-radius: 10px; padding: 10px; }
  [data-testid="stExpander"] { background: #161B22; border: 1px solid #30363D; }
  div[data-testid="stSelectbox"] > div { background: #161B22; border-color: #30363D; }
</style>
""", unsafe_allow_html=True)


# ── Sidebar navigation ──────────────────────────────────────────────────────
with st.sidebar:
    st.markdown(
        '<div style="text-align:center;padding:12px 0 16px">'
        '<div style="font-size:2rem">🌀</div>'
        '<div style="font-weight:700;color:#E6EDF3;font-size:1rem;line-height:1.2">'
        'Cyclone EWS</div>'
        '<div style="font-size:0.72rem;color:#8B949E">IBM Agentic AI Platform</div>'
        '</div>',
        unsafe_allow_html=True,
    )
    st.divider()

    st.markdown('<div style="font-size:0.68rem;color:#8B949E;text-transform:uppercase;'
                'letter-spacing:0.1em;padding:0 4px 4px">🛰️ Monitoring</div>',
                unsafe_allow_html=True)
    monitoring_page = st.radio("", [
        "🏠 Mission Control Dashboard",
    ], key="nav_monitor", label_visibility="collapsed")

    st.markdown('<div style="font-size:0.68rem;color:#8B949E;text-transform:uppercase;'
                'letter-spacing:0.1em;padding:8px 4px 4px">🤖 AI Agents</div>',
                unsafe_allow_html=True)
    agent_page = st.radio("", [
        "🌦️ Weather Analysis",
        "🔍 Cyclone Detection",
        "🗺️ Track & Prediction",
        "💥 Intensity Prediction",
        "⚠️ Impact Assessment",
        "🚨 Early Warning & Alerts",
        "🛟 Disaster Response",
    ], key="nav_agents", label_visibility="collapsed")

    st.markdown('<div style="font-size:0.68rem;color:#8B949E;text-transform:uppercase;'
                'letter-spacing:0.1em;padding:8px 4px 4px">🧠 Intelligence</div>',
                unsafe_allow_html=True)
    intel_page = st.radio("", [
        "🔬 LLM Comparison",
        "🔭 Observability",
        "📊 Performance Eval",
        "🛡️ Guardrails",
    ], key="nav_intel", label_visibility="collapsed")

    st.markdown('<div style="font-size:0.68rem;color:#8B949E;text-transform:uppercase;'
                'letter-spacing:0.1em;padding:8px 4px 4px">🗺️ Explorer</div>',
                unsafe_allow_html=True)
    explore_page = st.radio("", [
        "🌊 Coastal Zone Explorer",
    ], key="nav_explore", label_visibility="collapsed")

    st.markdown('<div style="font-size:0.68rem;color:#8B949E;text-transform:uppercase;'
                'letter-spacing:0.1em;padding:8px 4px 4px">⚖️ Governance</div>',
                unsafe_allow_html=True)
    gov_page = st.radio("", [
        "⚖️ AI Governance",
    ], key="nav_gov", label_visibility="collapsed")

    st.divider()
    st.markdown(
        '<div style="font-size:0.68rem;color:#8B949E;text-align:center;padding:4px 0">'
        'IBM Bob · IBM Granite · watsonx.ai</div>',
        unsafe_allow_html=True,
    )


# ── Determine active page from whichever radio was last changed ────────────
# Streamlit radio groups: detect which group is "active" by tracking the last
# group that differs from its default. We use a simple priority scheme:
# the last group with a non-first option selected wins, otherwise use group order.
def _active_group():
    agents = [
        "🌦️ Weather Analysis", "🔍 Cyclone Detection", "🗺️ Track & Prediction",
        "💥 Intensity Prediction", "⚠️ Impact Assessment",
        "🚨 Early Warning & Alerts", "🛟 Disaster Response",
    ]
    intels = ["🔬 LLM Comparison", "🔭 Observability", "📊 Performance Eval", "🛡️ Guardrails"]

    sel_monitor = st.session_state.get("nav_monitor", "🏠 Mission Control Dashboard")
    sel_agent   = st.session_state.get("nav_agents",  "🌦️ Weather Analysis")
    sel_intel   = st.session_state.get("nav_intel",   "🔬 LLM Comparison")
    sel_explore = st.session_state.get("nav_explore", "🌊 Coastal Zone Explorer")
    sel_gov     = st.session_state.get("nav_gov",     "⚖️ AI Governance")

    # Use explicit page tracking via a separate session key
    last = st.session_state.get("_last_nav_group", "monitor")
    return last, sel_monitor, sel_agent, sel_intel, sel_explore, sel_gov


# Track which group was most recently interacted with
for gkey, gval in [
    ("_last_nav_group_monitor", monitoring_page),
    ("_last_nav_group_agents",  agent_page),
    ("_last_nav_group_intel",   intel_page),
    ("_last_nav_group_explore", explore_page),
    ("_last_nav_group_gov",     gov_page),
]:
    if st.session_state.get(gkey) != gval:
        st.session_state[gkey] = gval
        st.session_state["_active_nav"] = gkey


active_nav = st.session_state.get("_active_nav", "_last_nav_group_monitor")

# ── Route to page ────────────────────────────────────────────────────────────
if active_nav == "_last_nav_group_agents":
    page_map = {
        "🌦️ Weather Analysis":    "pages.agents.agent1_weather",
        "🔍 Cyclone Detection":    "pages.agents.agent2_detection",
        "🗺️ Track & Prediction":  "pages.agents.agent3_tracking",
        "💥 Intensity Prediction": "pages.agents.agent4_intensity",
        "⚠️ Impact Assessment":   "pages.agents.agent5_impact",
        "🚨 Early Warning & Alerts": "pages.agents.agent6_warning",
        "🛟 Disaster Response":   "pages.agents.agent7_response",
    }
    mod = __import__(page_map[agent_page], fromlist=["render"])
    mod.render()

elif active_nav == "_last_nav_group_intel":
    page_map = {
        "🔬 LLM Comparison":  "pages.intelligence.llm_comparison",
        "🔭 Observability":   "pages.intelligence.observability",
        "📊 Performance Eval": "pages.intelligence.eval_dashboard",
        "🛡️ Guardrails":     "pages.intelligence.guardrails_dashboard",
    }
    mod = __import__(page_map[intel_page], fromlist=["render"])
    mod.render()

elif active_nav == "_last_nav_group_explore":
    from pages.explorer.zone_explorer import render
    render()

elif active_nav == "_last_nav_group_gov":
    from pages.governance.governance_dashboard import render
    render()

else:
    # Default — Mission Control Dashboard
    from pages.dashboard.main_dashboard import render
    render()
