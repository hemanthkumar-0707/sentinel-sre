"""
Sentinel SRE - Streamlit operations dashboard.

Run:  venv\\Scripts\\streamlit run app.py   (defaults to http://localhost:8501)

Tab 1 "Outage Simulator" runs the before/after diagnosis with the same
SentinelAgent used by demo.py; Tab 2 commits new post-mortems to the
Hindsight Cloud memory bank with real-time retention confirmation.
"""
import re

import streamlit as st

from agent import SentinelAgent, extract_metrics
import config

st.set_page_config(
    page_title="Sentinel SRE",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# --- Shared agent (cached so clients are reused across reruns) --------------- #
@st.cache_resource(show_spinner=False)
def get_agent() -> SentinelAgent:
    return SentinelAgent()


agent = get_agent()

ALERT_PRESETS = {
    "CRITICAL · Checkout 504 (pool exhaustion)": (
        "CRITICAL: HTTP 504 Gateway Timeout on checkout-service; "
        "PostgreSQL connection pool exhausted."
    ),
    "WARNING · Auth 500 (Redis OOM)": (
        "ALERT: HTTP 500 spike on /auth/v1/token; "
        "Redis OOM maxmemory reached."
    ),
    "✍️ Custom alert": "",
}

CUSTOM = "✍️ Custom alert"

# --- Custom CSS (spacing + card polish) -------------------------------------- #
st.markdown(
    """
    <style>
        .block-container { padding-top: 1.4rem; }
        div[data-testid="stMetric"] {
            background: rgba(118, 185, 0, 0.08);
            border: 1px solid rgba(118, 185, 0, 0.35);
            border-radius: 10px;
            padding: 12px 16px;
        }
        .sentinel-card {
            border: 1px solid rgba(118, 185, 0, 0.45);
            border-radius: 10px;
            padding: 14px 18px;
            background: linear-gradient(135deg, rgba(118,185,0,0.10), rgba(118,185,0,0.02));
        }
        .sentinel-code {
            font-size: 0.95em;
        }
    </style>
    """,
    unsafe_allow_html=True,
)

# --- Header ------------------------------------------------------------------ #
st.markdown("## 🛡️ Sentinel SRE — Autonomous Incident Diagnostics")
st.caption(
    "Battle-tested runbooks on demand: Hindsight persistent memory + NVIDIA Nemotron reasoning."
)

# --- Sidebar: system status cards -------------------------------------------- #
with st.sidebar:
    st.markdown("### ⚙️ System Status")
    st.markdown(
        f"""
        <div class="sentinel-card">
            <b>🧠 Reasoning Engine</b><br>
            <span style="opacity:0.85">NVIDIA Nemotron 3 Ultra 550B (NIM)</span><br><br>
            <b>🗄️ Persistent Memory</b><br>
            <span style="opacity:0.85">Vectorize Hindsight Cloud
            (Bank: <code>{config.HINDSIGHT_BANK_ID}</code>)</span><br><br>
            <b>📡 Node Status</b><br>
            <span style="color:#76B900">● Active (Graph Consolidated)</span>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("### 🌱 Continuous Learning")
    if st.button("Ingest Sample Runbooks into Memory", use_container_width=True):
        with st.spinner("Seeding bundled post-mortems into Hindsight…"):
            agent.seed_historical_data()
        st.success("Sample runbooks ingested / verified in the memory graph.")

    st.caption(
        "Recall → Diagnose → Retain. Every resolved incident makes the next "
        "one a one-click fix."
    )

# --- Main: two tabs ----------------------------------------------------------- #
tab_sim, tab_learn = st.tabs(["🚨 Outage Simulator (Before vs. After)", "🧠 Continuous Learning"])

# ------------------------------------------------------------------ Tab 1 ---- #
with tab_sim:
    choice = st.selectbox("Alert source", list(ALERT_PRESETS.keys()))
    if choice == CUSTOM:
        alert = st.text_area(
            "Custom incident alert",
            value="ALERT: high error rate on ",
            placeholder="Paste the actual pager message here…",
        )
    else:
        alert = ALERT_PRESETS[choice]
        st.text_area("Selected alert", value=alert, disabled=True)

    memory_on = st.toggle("Enable Hindsight Persistent Memory", value=True)

    if st.button("🚑 Diagnose Outage", type="primary", use_container_width=True):
        if not alert.strip():
            st.warning("Provide an alert (preset or custom) before diagnosing.")
        else:
            with st.spinner("Sentinel SRE is correlating the alert with memory and reasoning…" if memory_on
                            else "Running stateless baseline (memory disabled)…"):
                diagnosis = agent.diagnose(alert, use_memory=memory_on)
                st.session_state["diagnosis"] = diagnosis
                st.session_state["mem_state"] = memory_on

    diagnosis = st.session_state.get("diagnosis")
    mem_state = st.session_state.get("mem_state")

    if diagnosis:
        if not mem_state:
            st.error("🧠⌛ Stateless Mode: Generic Documentation Advice (Amnesia)")
            st.warning(
                "No persistent memory consulted — this is the 'first encounter' behaviour. "
                "The responder must re-investigate everything from scratch."
            )
            st.markdown(diagnosis)
        else:
            m = extract_metrics(diagnosis)
            success_label = (
                f"🎯 Precedent Matched: {m['matched']} via Vectorize Hindsight"
                if m["matched"] else "🆕 Uncatalogued incident — triage mode"
            )
            st.success(success_label)

            c1, c2, c3 = st.columns(3)
            c1.metric("Confidence", f"{m['confidence']}% Match" if m["confidence"] else "—")
            c2.metric("Matched", m["matched"] or "None")
            c3.metric(
                "MTTR Saved",
                f"~{m['mttr_saved_minutes']:.0f} min"
                if m["mttr_saved_minutes"] else "—",
                help=f"Manual triage ≈ {m['mttr_manual_minutes'] or '—'} min → "
                     f"automated runbook ≈ {m['mttr_auto_seconds'] or '—'} s",
            )

            if m["runbook"]:
                st.markdown("#### 📋 Historical Runbook (click any command to copy)")
                for item in m["runbook"]:
                    if item["comment"]:
                        st.markdown(f"<span class='sentinel-code' style='opacity:0.75'>"
                                    f"# {item['comment']}</span>", unsafe_allow_html=True)
                    else:
                        st.code(item["command"], language="bash")

            with st.expander("Full diagnosis (markdown)", expanded=False):
                st.markdown(diagnosis)

# ------------------------------------------------------------------ Tab 2 ---- #
with tab_learn:
    st.markdown(
        "Commit a newly resolved incident so the next occurrence is answered "
        "with the verified fix."
    )
    with st.form("retain_form", clear_on_submit=False):
        f_id = st.text_input("Incident ID", value="INC-2024-003", placeholder="INC-YYYY-NNN")
        f_service = st.text_input("Service affected", placeholder="e.g. payments-api")
        f_cause = st.text_area(
            "Root cause summary",
            placeholder="e.g. Kafka consumer group rebalances caused duplicate processing and idempotency-key storms on Dynamo…",
        )
        f_runbook = st.text_area(
            "Runbook commands (one per line)",
            placeholder="kubectl scale deployment/\nredis-cli --scan --pattern '…' | xargs …\nawS / psql steps…",
        )
        submitted = st.form_submit_button("💾 Commit to Hindsight Cloud Graph", type="primary")

    if submitted:
        missing = [
            name for name, val in
            [("Incident ID", f_id), ("Root cause", f_cause), ("Runbook", f_runbook)]
            if not val.strip()
        ]
        if missing:
            st.warning(f"Fill in: {', '.join(missing)}")
        else:
            summary = f"{f_service or 'service'}: {f_cause.strip()}"
            with st.spinner("Committing post-mortem to the Hindsight Cloud graph…"):
                result = agent.generate_and_retain_postmortem(
                    incident_id=f_id.strip().upper(),
                    summary=summary,
                    resolution=f_runbook.strip(),
                )
            if result["retained"]:
                verified = "✅ verified searchable" if result["verified"] else "⏳ indexing (retry recall shortly)"
                st.success(
                    f"🧠 {result['incident_id']} committed to bank "
                    f"**{result['bank']}** · "
                    f"tokens: **{result['tokens']}** · "
                    f"graph retention: **{verified}**"
                )
            else:
                st.error(f"Retention failed — see console logs for diagnostics ({result}).")