# Cyclone Detection & Early Warning System
## Development Notes

### Project Overview
Agentic AI-based Cyclone Detection & Early Warning System for Indian coastal regions  
(Bay of Bengal and Arabian Sea). Built using IBM Bob + IBM Granite LLM + IBM Cloud.

---

### Architecture

```
app.py                         ← Clean ~150-line router (sidebar nav + page dispatch)
├── pages/
│   ├── dashboard/
│   │   └── main_dashboard.py  ← Mission Control: animated map + KPIs + pipeline status
│   ├── agents/
│   │   ├── _agent_base.py     ← Shared helpers: header, how-it-works panel, report card
│   │   ├── agent1_weather.py
│   │   ├── agent2_detection.py
│   │   ├── agent3_tracking.py
│   │   ├── agent4_intensity.py
│   │   ├── agent5_impact.py
│   │   ├── agent6_warning.py
│   │   └── agent7_response.py
│   ├── intelligence/
│   │   ├── llm_comparison.py  ← Side-by-side LLM benchmarking
│   │   ├── observability.py   ← ReAct traces + token usage + memory state
│   │   ├── eval_dashboard.py  ← Re-exports pages/eval_dashboard.py
│   │   └── guardrails_dashboard.py ← Re-exports pages/guardrails_dashboard.py
│   ├── explorer/
│   │   └── zone_explorer.py   ← Re-exports pages/zone_explorer.py
│   └── governance/
│       └── governance_dashboard.py ← 15 policies + audit trail + regulatory alignment
│
├── agents/
│   ├── orchestrator.py        ← v3: 4-phase supervisor pipeline
│   ├── supervisor_agent.py    ← Hierarchical supervisor
│   ├── weather_analysis_agent.py   ← watsonx/LLaMA 3-70B
│   ├── cyclone_detection_agent.py  ← watsonx/LLaMA 3-70B
│   ├── tracking_agent.py           ← Gemini Pro
│   ├── intensity_agent.py          ← Groq/LLaMA 3-70B
│   ├── impact_agent.py             ← Gemini Pro
│   ├── warning_agent.py            ← Groq/LLaMA 3-70B
│   └── response_agent.py           ← watsonx/LLaMA 3-70B
│
├── gateway/
│   └── llm_client.py          ← Unified 5-provider client (watsonx, Gemini, Groq, Replicate, OpenRouter)
│
├── core/
│   ├── llm_router.py          ← Per-agent LLM assignment map
│   ├── react_engine.py        ← ReAct loop (Think→Act→Observe, max 3 iterations)
│   ├── prompt_optimizer.py    ← Token compression
│   └── output_verifier.py     ← Cross-agent consistency verification
│
├── memory/
│   ├── short_term.py          ← Session-scoped context buffer
│   ├── vector_store.py        ← ChromaDB long-term memory
│   └── knowledge_base.py      ← 8 domain facts seeded on first run
│
├── tools/
│   ├── registry.py            ← MCP tool registry with auto-registration
│   ├── weather_tools.py
│   ├── satellite_tools.py
│   ├── impact_tools.py
│   └── alert_tools.py
│
├── analytics/
│   ├── metrics_tracker.py     ← SQLite-persistent LLM call metrics
│   └── llm_comparator.py      ← Side-by-side LLM comparison engine
│
├── security/
│   ├── guardrails.py          ← Re-exports utils/guardrails.py
│   ├── nemo_guardrails.py     ← NeMo-style Colang rail shim
│   └── governance.py          ← 15 named policies + audit trail
│
├── data_layer/
│   └── data_generator.py      ← Synthetic data generators
│
└── utils/                     ← Legacy (kept for backward compat)
    ├── data_generator.py
    ├── guardrails.py          ← ORIGINAL working guardrails (9 categories, 40+ checks)
    ├── llm_client.py
    ├── metrics_tracker.py
    └── watsonx_client.py
```

---

### Per-Agent LLM Routing

| Agent | Provider | Model |
|-------|----------|-------|
| Weather Analysis | IBM watsonx | meta-llama/llama-3-3-70b-instruct |
| Cyclone Detection | IBM watsonx | meta-llama/llama-3-3-70b-instruct |
| Track & Prediction | Google Gemini | gemini-pro |
| Intensity Prediction | Groq Cloud | llama3-70b-8192 |
| Impact Assessment | Google Gemini | gemini-pro |
| Early Warning | Groq Cloud | llama3-70b-8192 |
| Disaster Response | IBM watsonx | meta-llama/llama-3-3-70b-instruct |

**Note:** IBM Granite models are not available in the eu-gb watsonx region.  
The gateway auto-detects the first available model. In eu-gb, this resolves to `meta-llama/llama-3-3-70b-instruct`.

---

### Orchestrator Pipeline (v3)

4 phases, each building on upstream context:

```
Phase 1 (parallel): Weather Analysis + Cyclone Detection
Phase 2 (parallel): Track & Prediction + Intensity Prediction  ← receives Phase 1
Phase 3 (parallel): Impact Assessment + Early Warning          ← receives Phase 2
Phase 4 (serial):   Disaster Response                          ← receives Phase 3
```

---

### Animated Cyclone Map

- Built with Plotly `frames` animation (`pages/dashboard/main_dashboard.py`)
- 13 frames × 6-hour intervals = T+0h to T+72h
- Cyclone eye pulses via `marker.size = 18 + 6*sin(frame*0.9)`
- Rotating spiral wind bands: layered concentric Scattergeo circles
- Track line draws itself frame-by-frame
- Intensity color shifts: Green → Yellow → Orange → Red (Cat 1→4)
- Time slider and Play/Pause buttons

---

### Guardrails (9 categories, 40+ checks)

`utils/guardrails.py` → `security/guardrails.py` (re-export)

1. **Input** — prompt injection, malicious content, PII, inappropriate content, input validation
2. **Output** — hallucination, factual accuracy, toxicity, sensitive information, format validation
3. **Tool** — tool permissions, function-call validation, call count limits
4. **Data** — data privacy, RBAC, PII masking, unauthorized retrieval prevention
5. **Security** — jailbreak detection, SQL injection, credential exposure, cross-agent trust
6. **Operational** — token budget, cost budget, agent iteration limits, rate limiting
7. **HITL** — human approval for critical actions, confidence-based escalation
8. **Multi-Agent** — loop detection, handoff validity, task assignment validation
9. **Ethical** — bias detection, fairness validation, regulatory compliance, audit trail

---

### Environment Variables (.env)

```
WATSONX_URL=https://eu-gb.ml.cloud.ibm.com
WATSONX_API_KEY=<your_key>
WATSONX_PROJECT_ID=<your_project_id>
GOOGLE_API_KEY=<your_gemini_key>
GROQ_API_KEY=<your_groq_key>
REPLICATE_API_TOKEN=<optional>
OPENROUTER_API_KEY=<optional>
```

---

### Running the App

```bash
streamlit run app.py
```

Runs on http://localhost:8501

---

### Data Sources

- **Synthetic** (default): `utils/data_generator.py` — realistic synthetic meteorological data
- **Real (future)**: IMD API, NOAA NCEI, NASA EOSDIS, OpenWeather API

---

### Technology Stack

- Python 3.12
- Streamlit (UI framework)
- IBM watsonx.ai (primary LLM — eu-gb region)
- Google Gemini Pro (tracking + impact agents)
- Groq Cloud (intensity + warning agents)
- ChromaDB (vector store / long-term memory)
- SQLite (metrics + audit trail persistence)
- Plotly (all charts + animated cyclone map)
- Pandas / NumPy (data processing)
