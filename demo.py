"""
Sentinel SRE - before/after persistent-memory demonstration.

Step 1: diagnose the live checkout 504 alert with memory DISABLED  -> generic advice.
Step 2: retain post-mortem INC-2024-001 into Hindsight             -> knowledge committed.
Step 3: diagnose the same alert with memory ENABLED                -> exact historical runbook.

Run:  venv\\Scripts\\python demo.py
"""
import json
import os

from agent import SentinelAgent, DATA_DIR, _postmortem_to_text
from core.memory_manager import close_client

ALERT = """
ALERT: checkout-service - 504 Gateway Timeout (firing)
- Service: checkout-service (Kubernetes, namespace: production)
- Symptoms: 95% of /checkout requests timing out at 30s, DB connection pool exhausted
- Error: "dial tcp: i/o timeout" in gateway logs
- Signal: Celery worker tasks stuck holding Redis locks, queue depth climbing
- Database: PostgreSQL (RDS), max_connections=200
"""

RULE = "=" * 72


def _load_inc_2024_001() -> dict:
    """Load the INC-2024-001 post-mortem record from the bundled dataset."""
    path = os.path.join(DATA_DIR, "inc_2024_001.json")
    with open(path, "r", encoding="utf-8") as fh:
        return json.load(fh)


def main() -> None:
    print(RULE)
    print("SENTINEL SRE - BEFORE/AFTER PERSISTENT-MEMORY DEMONSTRATION")
    print(RULE)

    agent = SentinelAgent()

    # -- Step 1 ------------------------------------------------------------ #
    print(f"\n{RULE}\nSTEP 1: DIAGNOSE WITH MEMORY DISABLED (first encounter - amnesia)\n{RULE}\n")
    print(agent.diagnose(ALERT, use_memory=False))

    # -- Step 2 ------------------------------------------------------------ #
    print(f"\n{RULE}\nSTEP 2: RETAIN POST-MORTEM INC-2024-001 INTO HINDSIGHT\n{RULE}\n")
    record = _load_inc_2024_001()
    agent.retain_postmortem(_postmortem_to_text(record), tags=record.get("tags", []))

    # -- Step 3 ------------------------------------------------------------ #
    print(f"\n{RULE}\nSTEP 3: DIAGNOSE SAME ALERT WITH MEMORY ENABLED (recurring incident)\n{RULE}\n")
    print(agent.diagnose(ALERT, use_memory=True))

    print(f"\n{RULE}\nDEMONSTRATION COMPLETE")
    print("Step 3 cites INC-2024-001 and reproduces the exact historical runbook.")
    print(RULE)


if __name__ == "__main__":
    try:
        main()
    finally:
        close_client()