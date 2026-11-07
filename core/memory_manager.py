"""
Sentinel SRE - Hindsight persistent memory manager.

Wraps the official hindsight-client SDK (retain / recall) against the
Hindsight Cloud memory bank configured in config.py.
"""
import time

from hindsight_client import Hindsight

import config

_hindsight = Hindsight(
    base_url=config.HINDSIGHT_API_URL,
    api_key=config.HINDSIGHT_API_KEY,
)


def _format_results(results, limit: int) -> str:
    """Render recalled facts as a compact memory-context block for the LLM."""
    if not results:
        return ""
    lines = ["### RELEVANT PAST INCIDENTS (retrieved via Hindsight persistent memory):\n"]
    for i, fact in enumerate(results[:limit], 1):
        meta = fact.metadata or {}
        lines.append(
            f"**Memory {i}** [{getattr(fact, 'type', 'fact')}] "
            f"(incident: {meta.get('incident_id', 'n/a')})\n"
            f"{fact.text}\n"
        )
    lines.append(
        "A validated historical fix exists above. Correlate this alert with it and "
        "output the EXACT historical remediation commands. If multiple recalled facts "
        "reference the same incident, prefer the entry with the complete runbook.\n"
    )
    return "\n".join(lines)


def recall_memories(query: str, limit: int = 3) -> str:
    """
    Semantic recall against the memory bank; returns formatted incident facts.

    Handles short indexing lag after a retain via a bounded retry loop.
    Returns an empty string when nothing relevant is found.
    """
    memory_text = ""
    for attempt in range(3):
        try:
            response = _hindsight.recall(
                bank_id=config.HINDSIGHT_BANK_ID,
                query=query,
                max_tokens=limit * 512,
            )
            results = (response.results or [])[:limit]
            memory_text = _format_results(results, limit)
            if memory_text:
                return memory_text
        except Exception as exc:
            print(f"[Hindsight Recall Error] {exc}")
        if attempt < 2:
            print(f"[Hindsight] Memory not ready (attempt {attempt + 1}/3), waiting 3s...")
            time.sleep(3)
    return ""


_last_retain_info = {"success": False, "items": 0, "tokens": None}


def retain_memory(
    content: str,
    metadata: dict = None,
    context: str = "post-mortem",
) -> bool:
    """
    Store content (plus metadata) permanently in the memory bank.

    Metadata values must be strings per the Hindsight API, so every value is
    stringified here. Returns True on success. Retention details (token count,
    item count) are captured and retrievable via get_last_retain_info().
    """
    global _last_retain_info
    try:
        response = _hindsight.retain(
            bank_id=config.HINDSIGHT_BANK_ID,
            content=content,
            context=context,
            metadata={str(k): str(v) for k, v in (metadata or {}).items()},
        )
        _last_retain_info = {
            "success": bool(response.success),
            "items": getattr(response, "items_count", 0),
            "tokens": getattr(getattr(response, "usage", None), "total_tokens", None),
            "bank": config.HINDSIGHT_BANK_ID,
        }
        print(
            f"[Hindsight Retain] success={response.success} "
            f"items={_last_retain_info['items']} "
            f"tokens={_last_retain_info['tokens']}"
        )
        return bool(response.success)
    except Exception as exc:
        _last_retain_info = {
            "success": False,
            "items": 0,
            "tokens": None,
            "bank": config.HINDSIGHT_BANK_ID,
            "error": str(exc),
        }
        print(f"[Hindsight Retain Error] {exc}")
        return False


def get_last_retain_info() -> dict:
    """Return details of the most recent retain operation (tokens, success)."""
    return dict(_last_retain_info)


def close_client() -> None:
    """Release the SDK's aiohttp session cleanly at process exit."""
    close = getattr(_hindsight, "close", None)
    if callable(close):
        try:
            close()
        except Exception:
            pass