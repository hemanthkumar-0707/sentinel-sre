"""
Sentinel SRE - Autonomous SRE diagnostic agent.

Combines Hindsight persistent memory (recall/retain) with NVIDIA Nemotron
reasoning. When memory hits, the diagnosis carries a confidence score, the
cited historical precedent, an estimated MTTR reduction, and the exact
historical runbook - so recurring incidents are answered in seconds, not hours.
"""
import glob
import json
import os
import re

import config
from core.llm_client import call_nemotron
from core.memory_manager import (
    recall_memories,
    retain_memory,
    get_last_retain_info,
)

PERSONA = """You are Sentinel SRE, an autonomous Site Reliability Engineering diagnostic agent.
Your role: analyse production incidents and output SPECIFIC, EXECUTABLE remediation commands.

Response format - ALWAYS start with these three exact lines:
Confidence: <0-100>% (estimated similarity to the historical precedent)
Matched Incident: <incident_id from memory, or None>
MTTR Reduction: <N> minutes (Manual Triage) -> <N> seconds (Automated Runbook)
If no memory matched, use exactly: Confidence: 0% / Matched Incident: None /
MTTR Reduction: not applicable (Uncatalogued Incident)

Then continue with the body:
DIAGNOSIS: what is happening - 2-4 sentences.
ROOT CAUSE: why it is happening - 2-4 sentences.
REMEDIATION: EXACT commands, one per line inside a single ```bash block,
with short # comments; only executable kubectl / redis-cli / psql / aws / curl steps.

Rules:
- If memory context is provided, CORRELATE the alert with past failures. If multiple
  recalled memories reference the same incident, prefer the one containing the
  complete resolution steps and cite its incident id in "Matched Incident:".
- If no memory exists, flag it as uncatalogued and provide systematic triage steps.
- NEVER give generic advice like "check logs" or "restart service" without specific commands."""

DATA_DIR = os.path.join("data", "postmortems")


class SentinelAgent:
    """Diagnostics agent backed by Hindsight memory + Nemotron reasoning."""

    def diagnose(self, alert: str, use_memory: bool = True) -> str:
        """
        Diagnose an incident alert.

        use_memory=True performs Hindsight semantic recall first and injects the
        retrieved post-mortem facts into the prompt; use_memory=False runs with
        memory disabled (stateless mode) to demonstrate generic, amnesiac output.
        """
        if use_memory:
            memory_block = recall_memories(alert)
            if not memory_block:
                memory_block = (
                    "\n### MEMORY CHECK: no relevant past incidents found in Hindsight.\n"
                    "This is an uncatalogued issue - provide systematic triage steps.\n"
                )
        else:
            memory_block = ""

        user_prompt = (
            f"INCIDENT ALERT:\n{alert}\n\n"
            f"{memory_block}\n\n"
            "Analyse this incident using the required response format."
        )
        return call_nemotron(PERSONA, user_prompt, temperature=0.2, max_tokens=1000)

    def retain_postmortem(self, postmortem_text: str, tags: list = None) -> bool:
        """Commit a resolved post-mortem to the Hindsight memory bank."""
        metadata = {"source": "sentinel-sre", "environment": "production"}
        if tags:
            metadata["tags"] = ",".join(tags)
        return retain_memory(postmortem_text, metadata=metadata, context="post-mortem")

    def generate_and_retain_postmortem(
        self,
        incident_id: str,
        summary: str,
        resolution: str,
    ) -> dict:
        """
        Automated post-mortem generator.

        Formats the given summary + resolution into the standardized SRE
        schema, retains it into the Hindsight bank, then verifies the incident
        is actually searchable in the bank before reporting success.

        Returns dict: {incident_id, retained, verified, tokens, bank}.
        """
        content = (
            f"INCIDENT {incident_id} (resolved)\n"
            f"Summary: {summary}\n"
            f"ROOT CAUSE & CONTEXT: {summary}\n"
            f"RESOLUTION (validated runbook):\n{resolution}"
        )
        metadata = {
            "incident_id": incident_id,
            "source": "sentinel-sre-dashboard",
            "environment": "production",
        }

        retained = retain_memory(content, metadata=metadata, context="post-mortem")

        verified = False
        if retained:
            recalled = recall_memories(f"{incident_id} {summary}", limit=3)
            verified = incident_id in recalled

        info = get_last_retain_info()
        return {
            "incident_id": incident_id,
            "retained": retained,
            "verified": verified,
            "tokens": info.get("tokens"),
            "bank": info.get("bank", config.HINDSIGHT_BANK_ID),
        }

    def seed_historical_data(self) -> None:
        """
        Load JSON post-mortems from data/postmortems/ and commit each to Hindsight.

        Skips incidents already present in the bank so the demo can be re-run
        without creating duplicates.
        """
        files = sorted(glob.glob(os.path.join(DATA_DIR, "*.json")))
        if not files:
            print("[Seed] No post-mortem files found in data/postmortems/")
            return

        for path in files:
            with open(path, "r", encoding="utf-8") as fh:
                record = json.load(fh)

            incident_id = record.get("incident_id", os.path.basename(path))
            existing = recall_memories(
                f"{incident_id} {record.get('title', '')}", limit=3
            )
            if incident_id in existing:
                print(f"[Seed] {incident_id} already in memory bank - skipping.")
                continue

            print(f"[Seed] Retaining {incident_id} from {os.path.basename(path)}...")
            self.retain_postmortem(
                _postmortem_to_text(record), tags=record.get("tags", [])
            )


def _postmortem_to_text(record: dict) -> str:
    """Flatten a post-mortem JSON record into readable memory content."""
    steps = "\n".join(record.get("resolution_runbook", []))
    symptoms = "; ".join(record.get("symptoms", []))
    return (
        f"INCIDENT {record.get('incident_id')} (resolved {record.get('date')})\n"
        f"Title: {record.get('title')}\n"
        f"Service: {record.get('service')} - environment: {record.get('environment')} "
        f"- severity: {record.get('severity')}\n"
        f"Symptoms: {symptoms}\n"
        f"ROOT CAUSE: {record.get('root_cause')}\n"
        f"RESOLUTION (validated runbook):\n{steps}\n"
        f"Validation result: {record.get('validation')}"
    )


def extract_metrics(diagnosis: str) -> dict:
    """
    Parse the structured header lines emitted by diagnose().

    Returns dict with keys: confidence (int|None), matched (str|None),
    mttr_manual_minutes (float|None), mttr_auto_seconds (float|None),
    mttr_saved_minutes (float|None), runbook (list[dict]) for one-click copy.
    """
    metrics = {
        "confidence": None,
        "matched": None,
        "mttr_manual_minutes": None,
        "mttr_auto_seconds": None,
        "mttr_saved_minutes": None,
        "runbook": [],
    }
    if not diagnosis:
        return metrics

    conf = re.search(r"Confidence:\s*(\d+)\s*%", diagnosis, re.IGNORECASE)
    metrics["confidence"] = int(conf.group(1)) if conf else None

    match = re.search(r"Matched Incident:\s*([A-Za-z0-9\-]+)", diagnosis)
    metrics["matched"] = (
        match.group(1)
        if match and match.group(1).lower() not in ({"none", "n/a", "na", "null"})
        else None
    )

    mttr_m = re.search(
        r"MTTR Reduction:\s*(\d+)\s*(minutes|mins|min|hour|hours)", diagnosis, re.IGNORECASE
    )
    if mttr_m:
        amount = float(mttr_m.group(1))
        unit = mttr_m.group(2).lower()
        metrics["mttr_manual_minutes"] = amount * 60 if unit.startswith("hour") else amount

    mttr_a = re.search(r"->\s*(\d+)\s*(seconds|secs|sec|minute|minutes|min)", diagnosis, re.IGNORECASE)
    if mttr_a:
        amount = float(mttr_a.group(1))
        unit = mttr_a.group(2).lower()
        metrics["mttr_auto_seconds"] = amount * 60 if unit.startswith("min") else amount

    if metrics["mttr_manual_minutes"] is not None and metrics["mttr_auto_seconds"] is not None:
        metrics["mttr_saved_minutes"] = round(
            metrics["mttr_manual_minutes"] - metrics["mttr_auto_seconds"] / 60.0, 1
        )

    # Extract the primary bash block as copyable, line-level commands.
    block = re.search(r"```bash\n(.*?)```", diagnosis, re.DOTALL)
    if block:
        for line in block.group(1).splitlines():
            cmd = line.strip()
            if not cmd:
                continue
            metrics["runbook"].append(
                {"comment": cmd[1:].strip(), "command": None} if cmd.startswith("#")
                else {"comment": None, "command": cmd}
            )
    return metrics