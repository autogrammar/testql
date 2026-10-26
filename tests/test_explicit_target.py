"""Exercise CLI target selection against two independent HTTP servers."""
from contextlib import contextmanager
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
from threading import Thread

from click.testing import CliRunner
import pytest

from testql.cli import cli


@contextmanager
def server(identity):
    requests = []

    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            requests.append(self.path)
            body = json.dumps({"server": identity}).encode()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def log_message(self, *args):
            pass

    http = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    thread = Thread(target=http.serve_forever, daemon=True)
    thread.start()
    try:
        yield f"http://127.0.0.1:{http.server_port}", requests
    finally:
        http.shutdown()
        http.server_close()
        thread.join(timeout=2)


@pytest.mark.parametrize("config", [
    "CONFIG[1]{key, value}:\n  base_url, {default}\n",
    "CONFIG:\n  base_url: {default}\n",
    'SET base_url "{default}"\n',
])
def test_cli_target_cannot_be_overwritten_by_scenario(tmp_path, config):
    with server("selected") as (selected, selected_requests), server("default") as (default, default_requests):
        path = tmp_path / "target.testql.toon.yaml"
        path.write_text(config.replace("{default}", default) + (
            'API GET ${base_url}/health\nASSERT_STATUS 200\nASSERT_JSON server == "selected"\n'
        ))
        result = CliRunner().invoke(cli, ["run", str(path), "--url", selected, "--quiet", "--output", "json"])

        assert result.exit_code == 0, result.output
        assert json.loads(result.output)["ok"] is True
        assert selected_requests == ["/health"]
        assert default_requests == []


def test_scenario_target_is_used_without_cli_override(tmp_path):
    with server("configured") as (default, requests):
        path = tmp_path / "default.testql.toon.yaml"
        path.write_text(f'''CONFIG[1]{{key, value}}:
  base_url, {default}
API GET ${{base_url}}/health
ASSERT_JSON server == "configured"
''')
        result = CliRunner().invoke(cli, ["run", str(path), "--quiet", "--output", "json"])

        assert result.exit_code == 0, result.output
        assert requests == ["/health"]


def test_cli_override_does_not_freeze_unrelated_variables(tmp_path):
    with server("selected") as (selected, requests):
        path = tmp_path / "variables.oql"
        path.write_text('''SET route "/first"
SET route "/health"
API GET ${base_url}${route}
ASSERT_JSON server == "selected"
''')
        result = CliRunner().invoke(cli, ["run", str(path), "--url", selected, "--quiet"])

        assert result.exit_code == 0, result.output
        assert requests == ["/health"]


def test_included_scenario_cannot_replace_cli_target(tmp_path):
    with server("selected") as (selected, selected_requests), server("default") as (default, default_requests):
        (tmp_path / "child.oql").write_text(f'SET base_url "{default}"\nAPI GET ${{base_url}}/health\n')
        path = tmp_path / "parent.oql"
        path.write_text('INCLUDE "child.oql"\nASSERT_JSON server == "selected"\n')
        result = CliRunner().invoke(cli, ["run", str(path), "--url", selected, "--quiet"])

        assert result.exit_code == 0, result.output
        assert selected_requests == ["/health"]
        assert default_requests == []
