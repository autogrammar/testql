"""Live LLM provider for conversation tests (optional, flaky — not for default CI)."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from typing import Any

import httpx

from testql.contracts.nlp2dsl_conversation import response_format, validate_payload


@dataclass
class LiveLLMProvider:
    """Call an OpenAI-compatible chat API to fill missing dialog fields."""

    api_key: str
    model: str = "openrouter/z-ai/glm-5.2"
    base_url: str = "https://openrouter.ai/api/v1"
    timeout_s: float = 60.0
    extra_headers: dict[str, str] = field(default_factory=dict)

    @classmethod
    def from_env(cls) -> "LiveLLMProvider":
        api_key = (
            os.environ.get("OPENROUTER_API_KEY") or os.environ.get("LLM_API_KEY") or ""
        )
        if not api_key:
            raise RuntimeError(
                "TESTQL_LIVE_LLM=1 requires OPENROUTER_API_KEY or LLM_API_KEY"
            )
        return cls(
            api_key=api_key,
            model=os.environ.get(
                "TESTQL_LIVE_LLM_MODEL",
                os.environ.get("LLM_MODEL", "openrouter/z-ai/glm-5.2"),
            ),
            base_url=os.environ.get(
                "TESTQL_LIVE_LLM_BASE_URL",
                os.environ.get("LLM_BASE_URL", "https://openrouter.ai/api/v1"),
            ).rstrip("/"),
        )

    def reply_for(
        self,
        conversation_id: str,
        *,
        missing: list[str] | None = None,
        context: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        prompt = self._build_prompt(
            conversation_id, missing=missing or [], context=context or {}
        )
        content = self._chat(prompt)
        payload = self._parse_json_object(content)
        fields = payload["fields"]
        unexpected = set(fields) - set(missing or [])
        if missing and unexpected:
            names = ", ".join(sorted(unexpected))
            raise ValueError(f"live LLM returned fields outside missing set: {names}")
        return fields

    def _build_prompt(
        self, conversation_id: str, *, missing: list[str], context: dict[str, Any]
    ) -> str:
        return (
            "You are completing missing fields for an automated integration test.\n"
            f"conversationId: {conversation_id}\n"
            f"missing fields: {missing}\n"
            f"context: {json.dumps(context, ensure_ascii=False)}\n"
            "Respond with a ConversationFields 1.0.0 JSON object only. "
            "Put values under fields; keys must address the missing fields "
            "(e.g. attachmentPath, recipient). No markdown."
        )

    def _chat(self, prompt: str) -> str:
        url = f"{self.base_url}/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "X-Title": os.environ.get("OPENROUTER_APP_NAME", "").strip()
            or os.path.basename(os.getcwd())
            or "testql",
            **self.extra_headers,
        }
        site_url = os.environ.get("OPENROUTER_SITE_URL", "").strip()
        if site_url and "HTTP-Referer" not in headers:
            headers["HTTP-Referer"] = site_url
        payload = {
            "model": self.model.removeprefix("openrouter/"),
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0,
            "response_format": response_format(),
        }
        with httpx.Client(timeout=self.timeout_s) as client:
            response = client.post(url, headers=headers, json=payload)
            response.raise_for_status()
            data = response.json()
        choices = data.get("choices") or []
        if not choices:
            raise RuntimeError("live LLM returned no choices")
        message = choices[0].get("message") or {}
        content = message.get("content")
        if not isinstance(content, str) or not content.strip():
            raise RuntimeError("live LLM returned empty content")
        return content.strip()

    @staticmethod
    def _parse_json_object(text: str) -> dict[str, Any]:
        try:
            parsed = json.loads(text)
        except json.JSONDecodeError as exc:
            raise ValueError("live LLM response must be a single JSON object") from exc
        if not isinstance(parsed, dict):
            raise ValueError("live LLM response must be a JSON object")
        validate_payload(parsed)
        return parsed
