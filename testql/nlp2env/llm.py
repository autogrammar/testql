"""Optional LLM backend for source=llm nlp2env prompts."""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any, cast

from testql.contracts.nlp2env import (
    load_schema,
    openai_response_format,
    validate_tool_call,
)

_SYSTEM = """\
You translate natural-language user requests (any language) into nlp2env MCP tool calls for SMTP/email .env configuration.
Return ONLY JSON matching the nlp2env ToolCall 1.0.0 contract, no markdown:
{"contractVersion":"1.0.0","tool":"nlp2env_set_email","arguments":{"host":"smtp.example.com","user":"a@b.c","port":"587","from_addr":"a@b.c","password_env":"SMTP_PASSWORD"}}

Allowed tools: nlp2env_set_email, nlp2env_email_status, nlp2env_list.
Never put passwords in JSON — always use password_env=SMTP_PASSWORD.
Extract host, user/email, port from the user message regardless of language.
"""


def ollama_reachable(base: str | None = None) -> bool:
    url = (base or os.getenv("OLLAMA_API_BASE", "http://localhost:11434")).rstrip("/")
    try:
        with urllib.request.urlopen(f"{url}/api/tags", timeout=3) as resp:
            return resp.status == 200
    except (OSError, urllib.error.URLError):
        return False


def resolve_llm_backend() -> tuple[str, str]:
    key = os.getenv("OPENROUTER_API_KEY", "").strip()
    if key:
        model = os.getenv(
            "LLM_MODEL", os.getenv("PFIX_MODEL", "openrouter/z-ai/glm-5.2")
        )
        if not model.startswith("openrouter/"):
            model = f"openrouter/{model.removeprefix('ollama/')}"
        return "openrouter", model
    if ollama_reachable():
        model = os.getenv("PFIX_MODEL", os.getenv("LLM_MODEL", "ollama/gemma4:e4b"))
        if not model.startswith("ollama/"):
            model = f"ollama/{model}"
        return "ollama", model
    return "none", ""


def _http_post_json(
    url: str, payload: dict[str, Any], headers: dict[str, str] | None = None
) -> dict[str, Any]:
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=data,
        headers={"Content-Type": "application/json", **(headers or {})},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=120) as resp:
        return json.loads(resp.read().decode("utf-8"))


def _extract_json_object(text: str) -> dict[str, Any]:
    try:
        parsed = json.loads(text)
    except json.JSONDecodeError as exc:
        raise ValueError("LLM response must be a single JSON object") from exc
    if not isinstance(parsed, dict):
        raise TypeError("LLM response must be a JSON object")
    validate_tool_call(parsed)
    return parsed


def _openrouter_headers(api_key: str) -> dict[str, str]:
    app_name = (
        os.getenv("OPENROUTER_APP_NAME", "").strip() or Path.cwd().name or "testql"
    )
    headers = {
        "Authorization": f"Bearer {api_key}",
        "X-Title": app_name,
    }
    app_url = (
        os.getenv("OPENROUTER_APP_URL", "").strip()
        or os.getenv("OPENROUTER_SITE_URL", "").strip()
    )
    if app_url:
        headers["HTTP-Referer"] = app_url
    return headers


def translate_nl_to_mcp(
    nl: str, backend: str, model: str
) -> tuple[str, dict[str, str]]:
    messages = [
        {"role": "system", "content": _SYSTEM},
        {"role": "user", "content": nl},
    ]
    if backend == "openrouter":
        key = os.getenv("OPENROUTER_API_KEY", "").strip()
        body = _http_post_json(
            "https://openrouter.ai/api/v1/chat/completions",
            {
                "model": model.removeprefix("openrouter/"),
                "messages": messages,
                "temperature": 0.1,
                "response_format": openai_response_format(),
            },
            headers=_openrouter_headers(key),
        )
        content = body["choices"][0]["message"]["content"]
    elif backend == "ollama":
        base = os.getenv("OLLAMA_API_BASE", "http://localhost:11434").rstrip("/")
        body = _http_post_json(
            f"{base}/api/chat",
            {
                "model": model.removeprefix("ollama/"),
                "messages": messages,
                "stream": False,
                "format": load_schema(),
            },
        )
        content = body["message"]["content"]
    else:
        raise RuntimeError("Brak backendu LLM (OPENROUTER_API_KEY lub Ollama)")

    parsed = _extract_json_object(content)
    return cast(str, parsed["tool"]), cast(dict[str, str], parsed["arguments"])
