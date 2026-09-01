"""Shared, bounded parsing for HTTP response bytes."""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from typing import Any, Mapping

_TEXT_SNIPPET_LIMIT = 8192
_JSON_MEDIA_TYPES = frozenset({"application/json", "text/json"})
_TEXT_MEDIA_TYPES = frozenset({
    "application/javascript",
    "application/xml",
    "image/svg+xml",
})
_BINARY_MEDIA_TYPES = frozenset({
    "application/gzip",
    "application/octet-stream",
    "application/pdf",
    "application/zip",
})
_BINARY_SIGNATURES = (
    (b"\x89PNG\r\n\x1a\n", "png"),
    (b"%PDF-", "pdf"),
    (b"\xff\xd8\xff", "jpeg"),
    (b"GIF87a", "gif"),
    (b"GIF89a", "gif"),
    (b"PK\x03\x04", "zip"),
    (b"PK\x05\x06", "zip"),
    (b"\x1f\x8b", "gzip"),
)


@dataclass(frozen=True, slots=True)
class ParsedHttpBody:
    """Compatibility payload plus deterministic evidence about the raw body."""

    data: dict[str, Any]
    evidence: dict[str, Any]


def _content_type(headers: Mapping[str, Any]) -> str:
    for name, value in headers.items():
        if str(name).casefold() == "content-type":
            return str(value).split(";", 1)[0].strip().casefold()
    return ""


def _charset(headers: Mapping[str, Any]) -> str:
    for name, value in headers.items():
        if str(name).casefold() != "content-type":
            continue
        match = re.search(r"(?:^|;)\s*charset=([^;\s]+)", str(value), re.I)
        if match:
            return match.group(1).strip('"\'')
    return "utf-8"


def _is_json_media_type(content_type: str) -> bool:
    return content_type in _JSON_MEDIA_TYPES or content_type.endswith("+json")


def _is_text_media_type(content_type: str) -> bool:
    return (
        content_type.startswith("text/")
        or content_type in _TEXT_MEDIA_TYPES
        or content_type.endswith("+xml")
    )


def _is_binary_media_type(content_type: str) -> bool:
    return (
        content_type in _BINARY_MEDIA_TYPES
        or content_type.startswith(("audio/", "font/", "video/"))
        or (
            content_type.startswith("image/")
            and content_type != "image/svg+xml"
        )
    )


def _binary_magic(raw: bytes) -> str | None:
    for signature, name in _BINARY_SIGNATURES:
        if raw.startswith(signature):
            return name
    return None


def _magic(raw: bytes, content_type: str, kind: str) -> str:
    binary_magic = _binary_magic(raw)
    if binary_magic:
        return binary_magic
    if content_type == "image/svg+xml" or b"<svg" in raw[:1024].lower():
        return "svg"
    if kind == "json":
        return "json"
    if kind == "text":
        return "text"
    return "unknown"


def _looks_like_text(raw: bytes) -> bool:
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError:
        return False
    return not any(ord(char) < 32 and char not in "\t\r\n" for char in text)


def _evidence(raw: bytes, content_type: str, kind: str) -> dict[str, Any]:
    return {
        "kind": kind,
        "content_type": content_type,
        "byte_length": len(raw),
        "sha256": hashlib.sha256(raw).hexdigest(),
        "magic": _magic(raw, content_type, kind),
    }


def _json_payload(raw: bytes, headers: Mapping[str, Any]) -> dict[str, Any] | None:
    try:
        decoded = raw.decode(_charset(headers))
        parsed = json.loads(decoded)
    except (LookupError, UnicodeDecodeError, json.JSONDecodeError):
        return None
    return parsed if isinstance(parsed, dict) else {"data": parsed}


def parse_http_body(raw: bytes, headers: Mapping[str, Any]) -> ParsedHttpBody:
    """Classify raw bytes before decoding and retain bounded response evidence."""
    content_type = _content_type(headers)
    if not raw:
        return ParsedHttpBody({}, _evidence(raw, content_type, "empty"))

    if _binary_magic(raw) or _is_binary_media_type(content_type):
        return ParsedHttpBody({}, _evidence(raw, content_type, "binary"))

    looks_like_json = raw.lstrip().startswith((b"{", b"["))
    if _is_json_media_type(content_type) or looks_like_json:
        payload = _json_payload(raw, headers)
        if payload is not None:
            return ParsedHttpBody(payload, _evidence(raw, content_type, "json"))

    if _is_text_media_type(content_type) or _looks_like_text(raw):
        try:
            text = raw.decode(_charset(headers), errors="replace")
        except LookupError:
            text = raw.decode("utf-8", errors="replace")
        return ParsedHttpBody(
            {"text": text[:_TEXT_SNIPPET_LIMIT]},
            _evidence(raw, content_type, "text"),
        )

    return ParsedHttpBody({}, _evidence(raw, content_type, "binary"))


__all__ = ["ParsedHttpBody", "parse_http_body"]
