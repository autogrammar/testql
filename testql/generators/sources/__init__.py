"""testql.generators.sources — convert external artifacts into Unified IR.

Each source class implements `BaseSource`. The module-level `SOURCES` mapping
is auto-populated from the bundled built-ins and used by `pipeline.run()`.
Externally packaged sources (e.g. `graphql2testql`) register through the
`testql.sources` entry-point group and are resolved lazily by `get_source`.
"""

from __future__ import annotations

import sys
from importlib import metadata as importlib_metadata
from pathlib import Path
from typing import Optional

from .base import BaseSource, SourceLike
from .config_source import ConfigSource
from .conversation import ConversationTestSource
from .nl_source import NLSource
from .openapi_source import OpenAPISource
from .oql_source import OqlSource
from .oql_models import OqlCommand, ParsedScenario
from .oql_parser import OqlParser
from .pytest_source import PytestSource
from .ui_source import UISource
from .page_source import PageSource


_BUILTIN: dict[str, type[BaseSource]] = {
    "openapi": OpenAPISource,
    "nl": NLSource,
    "ui": UISource,
    "page": PageSource,
    "pytest": PytestSource,
    "oql": OqlSource,
    "conversation": ConversationTestSource,
    "nlp2dsl": ConversationTestSource,
}

_CONFIG_ALIASES = ("config", "makefile", "taskfile", "docker-compose", "buf")
_SOURCE_CHECKOUT_SOURCES = {
    "graphql": "graphql2testql.source:GraphQLSource",
    "proto": "proto2testql.source:ProtoSource",
    "sql": "sql2testql.source:SqlSource",
}


def _source_checkout_src(module_name: str) -> Path:
    return Path(__file__).resolve().parents[3] / "packages" / module_name / "src"


def _get_config_source() -> type[BaseSource]:
    """Lazy import to avoid circular dependency."""
    from .config_source import ConfigSource
    return ConfigSource


def _plugin_entry_points(group: str = "testql.sources"):
    entry_points = importlib_metadata.entry_points()
    if hasattr(entry_points, "select"):
        return entry_points.select(group=group)
    return entry_points.get(group, [])


def _get_plugin_source(key: str) -> Optional[type[BaseSource]]:
    for entry_point in _plugin_entry_points():
        if entry_point.name == key:
            return entry_point.load()
    fallback = _SOURCE_CHECKOUT_SOURCES.get(key)
    if fallback is not None:
        module_name, _, attr = fallback.partition(":")
        try:
            module = __import__(module_name, fromlist=[attr])
        except ImportError:
            src = _source_checkout_src(module_name)
            if not src.is_dir():
                return None
            sys.path.insert(0, str(src))
            try:
                module = __import__(module_name, fromlist=[attr])
            except ImportError:
                return None
        return getattr(module, attr)
    return None


def get_source(name: str) -> Optional[BaseSource]:
    """Instantiate a registered source by name (e.g. "openapi")."""
    key = name.lower()
    cls = _BUILTIN.get(key)
    if cls is None and key in _CONFIG_ALIASES:
        cls = _get_config_source()
    if cls is None:
        cls = _get_plugin_source(key)
    if cls is None:
        return None
    if cls is ConversationTestSource:
        return cls(name=key)
    return cls()


def available_sources() -> list[str]:
    plugin_names = {ep.name for ep in _plugin_entry_points()}
    for name in _SOURCE_CHECKOUT_SOURCES:
        if _get_plugin_source(name) is not None:
            plugin_names.add(name)
    return sorted(set(_BUILTIN.keys()) | set(_CONFIG_ALIASES) | plugin_names)


__all__ = [
    "BaseSource",
    "SourceLike",
    "OpenAPISource",
    "NLSource",
    "UISource",
    "PageSource",
    "PytestSource",
    "ConversationTestSource",
    "OqlSource",
    "OqlCommand",
    "ParsedScenario",
    "OqlParser",
    "get_source",
    "available_sources",
]
