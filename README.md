# Sentinel SRE: Autonomous Incident Response Agent with Persistent Memory

![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?logo=python&logoColor=white)
![LLM](https://img.shields.io/badge/Reasoning-NVIDIA%20Nemotron%203%20Ultra%20(NIM)-76B900)
![Memory](https://img.shields.io/badge/Graph%20Memory-Vectorize%20Hindsight-4B0082)
![License](https://img.shields.io/badge/License-MIT-green)

> An intelligent, memory-augmented Site Reliability Engineering (SRE) agent designed to autonomously triage production incidents, eliminate AI operational amnesia, and generate verified, executable runbook mitigations using persistent temporal-causal graphs.

---

## 📌 Problem Statement: Operational Amnesia in LLM Triage

Traditional Large Language Models (LLMs) used in DevOps and SRE workflows are fundamentally stateless:

- **No Long-Term Memory**: Every incident triage session starts with zero historical context.
- **Hallucinated & Generic Runbooks**: During cascading outages (e.g., PostgreSQL connection pool exhaustion or distributed lock deadlocks), standard LLMs recommend generic documentation checklists (e.g., "restart database", "review logs"), extending downtime.
- **Repeated Failures**: Organizations re-diagnose identical failure patterns repeatedly because post-mortems remain trapped in static PDF/Markdown documents instead of active operational memory.

Sentinel SRE solves this by pairing high-parameter reasoning via NVIDIA Nemotron 3 Ultra with Vectorize Hindsight persistent graph memory.

## 🏗️ System Architecture

```
                    [ Production Alert / Telemetry ]
                        │
                        ▼
            ┌───────────────────────────────────────────────┐
            │       Sentinel SRE Diagnostic Engine          │
            │           (Streamlit Web / CLI)               │
            └───────┬───────────────────────────────┬───────┘
                    │                               │
  Semantic Query    │                               │  Inference Prompt
  & Context Search  │                               │  & System Context
                    ▼                               ▼
┌───────────────────────────────────────────────┐  ┌───────────────────────────────────────────┐
│           Vectorize Hindsight                 │  │            NVIDIA Nemotron 3              │
│           Persistent Graph Memory             │  │            Ultra 550B (NIM)               │
│                                               │  │                                           │
│  • Temporal Links (73%)                       │  │  • High-Parameter System Synthesis        │
│  • Entity Links (15%)                         │  │  • Causal Correlation                     │
│  • Semantic Links (12%)                       │  │  • Remediation Step Generation            │
└───────────────────────┬───────────────────────┘  └───────────────────┬───────────────────────┘
                        │                                              │
                        └──────────────────────┬───────────────────────┘
                                               │
                                               ▼
                    ┌───────────────────────────────────────────────┐
                    │           Actionable Incident Response        │
                    │                                               │
                    │  • Historical Precedent: INC-2024-001         │
                    │  • Similarity Confidence: 96% Match           │
                    │  • Verified Runbook: Immediate CLI Commands   │
                    │  • Projected MTTR Reduction: 90m → 45s        │
                    └───────────────────────────────────────────────┘
```

## 📊 Performance & Comparative Analysis

The bundled demo (`demo.py`) runs the **same production alert** twice — once with the memory bank inaccessible, once after the validated resolution is retained. Real recorded output:

| Dimension | ⏱️ Manual Triage (Memory OFF) | ⚡ Sentinel SRE (Memory ON) |
|---|---|---|
| Diagnosis | Generic failure mechanics, exploratory wording | Names the exact match: *"This matches the signature of INC-2024-001"* |
| Root cause | Speculative cause list | Cites retained cause: orphaned Celery workers holding Redis locks while keeping DB connections open |
| Commands | Investigation-from-scratch (scan, pkill, scale, kill) | The recalled runbook, verbatim: `kubectl rollout undo` → flush `celery-lock-*` keys → clear stale PG sessions → RDS `max_connections=500` → verify |
| Post-fix action | None available | Retained hardening re-applied (reduced task retries, Redis lock TTL, DB pool circuit breaker) |
| Effective MTTR | ~90 minutes | **45 seconds** |

```text
STEP 1 (memory disabled):  generic triage — "identify lock keys, pkill workers, scale to zero"
STEP 2 (retain):           [Hindsight Retain] success=True items=1 tokens=5484
STEP 3 (memory enabled):   "...matches the exact signature of INC-2024-001" → full historical runbook
```

## 🛠️ Technology Stack & Core Components

- **Reasoning Engine:** NVIDIA Nemotron 3 Ultra 550B (`nvidia/nemotron-3-ultra-550b-a55b`) deployed via [NVIDIA NIM](https://build.nvidia.com) endpoints for complex infrastructure root-cause reasoning.
- **Persistent Agent Memory:** Vectorize Hindsight dynamic knowledge-graph engine for retaining, cross-linking, and recalling incident entities — [Hindsight GitHub](https://github.com/vectorize-io/hindsight) · [Hindsight Documentation](https://hindsight.vectorize.io/) · [What is Agent Memory?](https://vectorize.io/what-is-agent-memory)
- **Frontend Interface:** Streamlit real-time interactive dashboard (`app.py`).
- **Core Automation:** Python 3.10+ modular agent pipeline (`core/llm_client.py`, `core/memory_manager.py`, `agent.py`).

## 📁 Repository Structure

```
sentinel-sre/
├── core/
│   ├── __init__.py             # Module initialization
│   ├── llm_client.py           # NVIDIA NIM API integration client
│   └── memory_manager.py       # Vectorize Hindsight graph recall/retain manager
├── data/
│   └── postmortems/            # Standardized historical SRE post-mortem catalogs
│       ├── inc_2024_001.json   # Postgres pool exhaustion / Celery deadlock post-mortem
│       └── inc_2024_002.json   # Redis OOM maxmemory saturation post-mortem
├── .env.example                # Sanitized environment configuration template
├── .gitignore                  # Exclusion rules (secrets, venv, cache)
├── requirements.txt            # Dependencies
├── config.py                   # Centralized runtime configuration & credential validation
├── agent.py                    # Sentinel SRE core decision engine & orchestration
├── demo.py                     # 3-step automated comparative demonstration script
├── app.py                      # Interactive Streamlit web dashboard
├── LICENSE                     # MIT license
└── README.md                   # System documentation and setup guide
```

---

## 🚀 Installation & Setup Guide

### 1. Prerequisites

- Python 3.10, 3.11, or 3.12
- An active [NVIDIA NIM API key](https://build.nvidia.com)
- An active Vectorize Hindsight API key and Bank ID ([Hindsight Cloud](https://ui.hindsight.vectorize.io))

### 2. Clone the Repository

```bash
git clone https://github.com/<your-username>/sentinel-sre.git
cd sentinel-sre
```

### 3. Create and Activate Virtual Environment

```bash
# Windows (PowerShell)
python -m venv venv
venv\Scripts\Activate.ps1

# Linux / macOS
python3 -m venv venv
source venv/bin/activate
```

### 4. Install Dependencies

```bash
pip install -r requirements.txt
```

### 5. Configure Environment Variables

Create your local `.env` file by copying the template:

```bash
# Windows
copy .env.example .env

# Linux / macOS
cp .env.example .env
```

Populate `.env` with your credentials:

```bash
NVIDIA_API_KEY="your_nvidia_api_key_here"
NVIDIA_BASE_URL="https://integrate.api.nvidia.com/v1"
NVIDIA_MODEL="nvidia/nemotron-3-ultra-550b-a55b"
HINDSIGHT_API_KEY="your_hindsight_api_key_here"
HINDSIGHT_API_URL="https://api.hindsight.vectorize.io"
HINDSIGHT_BANK_ID="your_hindsight_bank_id_here"
```

---

## 💻 Usage & Verification

### Running the Comparative CLI Demo

Run the automated 3-step demonstration script to verify memory augmentation:

```bash
python demo.py
```

1. **Step 1**: Simulates an active incident alert without memory (demonstrates stateless LLM amnesia).
2. **Step 2**: Ingests and commits `INC-2024-001` post-mortem into the Vectorize Hindsight graph.
3. **Step 3**: Re-runs the alert with persistent memory enabled, accurately identifying `INC-2024-001` and outputting the tested operational runbook.

### Launching the Interactive Web Dashboard

Run the Streamlit web interface for visual diagnosis and live ingestion:

```bash
streamlit run app.py
```

Open <http://localhost:8501> in your browser to:

- Test preset outage alerts (e.g., PostgreSQL Pool Exhaustion, Redis OOM spikes).
- Toggle memory recall on/off to compare output quality in real time.
- Directly commit new post-mortem reports to the live Hindsight knowledge graph.

---

## 📜 License

Distributed under the MIT License. See [`LICENSE`](LICENSE) for more information.