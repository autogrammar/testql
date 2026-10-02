"""Unit tests for including TestTOON scenarios via INCLUDE."""

from __future__ import annotations

from pathlib import Path

from testql.interpreter import OqlInterpreter
from testql.interpreter._parser import OqlLine


def test_cmd_include_parses_testtoon_scenario(tmp_path: Path) -> None:
    """INCLUDE command should auto-detect and parse .testql.toon.yaml files."""
    sub_file = tmp_path / "sub.testql.toon.yaml"
    sub_file.write_text(
        """# SUB SCENARIO
CONFIG[1]{key, value}:
  my_var,  "hello_include"

API[1]{method, endpoint, status}:
  GET,  /test,  200
""",
        encoding="utf-8",
    )

    interp = OqlInterpreter(
        api_url="http://localhost:8100",
        dry_run=True,
        quiet=True,
        include_paths=[str(tmp_path)],
    )

    line = OqlLine(number=1, command="INCLUDE", args=f'"{sub_file.name}"', raw=f'INCLUDE "{sub_file.name}"')
    interp._cmd_include(line.args, line)

    assert interp.vars.get("my_var") == "hello_include"
    assert len(interp.errors) == 0
