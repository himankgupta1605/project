"""Thin wrapper around the Anthropic API used for research and copywriting.

Kept as a single narrow interface so the rest of the app never touches the
SDK directly - swapping providers later only means editing this file.
"""

from __future__ import annotations

import json
import os
import re
from typing import Optional

from brandpost.config import DEFAULT_LLM_MODEL


class LLMNotConfigured(RuntimeError):
    pass


def _api_key(explicit_key: Optional[str] = None) -> Optional[str]:
    return explicit_key or os.environ.get("ANTHROPIC_API_KEY")


def is_configured(explicit_key: Optional[str] = None) -> bool:
    return bool(_api_key(explicit_key))


def generate_text(
    prompt: str,
    system: str = "",
    max_tokens: int = 1500,
    api_key: Optional[str] = None,
    model: str = DEFAULT_LLM_MODEL,
) -> str:
    key = _api_key(api_key)
    if not key:
        raise LLMNotConfigured(
            "No Anthropic API key found. Set ANTHROPIC_API_KEY or enter a key in the sidebar."
        )
    import anthropic

    client = anthropic.Anthropic(api_key=key)
    response = client.messages.create(
        model=model,
        max_tokens=max_tokens,
        system=system or None,
        messages=[{"role": "user", "content": prompt}],
    )
    return "".join(block.text for block in response.content if block.type == "text")


def generate_json(
    prompt: str,
    system: str = "",
    max_tokens: int = 1500,
    api_key: Optional[str] = None,
    model: str = DEFAULT_LLM_MODEL,
) -> dict | list:
    """Ask the model for JSON and parse it, tolerating stray markdown fences."""
    full_system = (system + "\n\n" if system else "") + (
        "Respond with ONLY valid JSON. No markdown fences, no commentary."
    )
    raw = generate_text(prompt, system=full_system, max_tokens=max_tokens, api_key=api_key, model=model)
    raw = raw.strip()
    match = re.search(r"```(?:json)?\s*(.*?)```", raw, re.DOTALL)
    if match:
        raw = match.group(1).strip()
    return json.loads(raw)
