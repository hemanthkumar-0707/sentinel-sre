"""
Sentinel SRE - NVIDIA Nemotron LLM client.

Thin wrapper around the OpenAI-compatible NVIDIA NIM endpoint
(https://integrate.api.nvidia.com/v1) defined in config.py.
"""
from openai import OpenAI

import config

_client = OpenAI(
    base_url=config.NVIDIA_BASE_URL,
    api_key=config.NVIDIA_API_KEY,
)


def call_nemotron(
    system_prompt: str,
    user_prompt: str,
    temperature: float = 0.2,
    max_tokens: int = 600,
) -> str:
    """
    Send a system + user prompt pair to Nemotron and return the completion text.

    Args:
        system_prompt: Operational persona / rule set.
        user_prompt: Incident alert + optional retrieved memory context.
        temperature: Sampling temperature (low for deterministic SRE output).
        max_tokens: Response length cap.

    Returns:
        The model's response text, or an error string prefixed with
        "[Nemotron Error]" if the call fails.
    """
    try:
        response = _client.chat.completions.create(
            model=config.NVIDIA_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=temperature,
            max_tokens=max_tokens,
        )
        return response.choices[0].message.content
    except Exception as exc:  # surface API failures without crashing the demo
        return f"[Nemotron Error] {exc}"