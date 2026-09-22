"""Resilience tests for optional nlp2env imports."""

from __future__ import annotations

import importlib
import sys


def test_testql_cli_imports_without_nlp2env():
    """Verify testql.cli can be imported even when nlp2env package is not present."""
    # Ensure nlp2env is not in sys.modules
    sys.modules.pop("nlp2env", None)
    sys.modules.pop("nlp2env.toon_scenarios", None)

    # testql.cli imports commands including nlp2env_cmd
    mod = importlib.import_module("testql.cli")
    assert mod.main is not None


def test_nlp2env_getattr_fallback():
    """Verify testql.nlp2env.__getattr__ returns None or loads cleanly."""
    import testql.nlp2env as nlp_mod

    # PromptScenario should not raise an unhandled error when nlp2env is missing
    scenario_cls = getattr(nlp_mod, "PromptScenario")
    # If nlp2env is not installed, it returns None
    assert scenario_cls is None or hasattr(scenario_cls, "__name__")
