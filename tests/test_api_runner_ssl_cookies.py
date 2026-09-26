"""Unit tests for SSL, cookie jar and CSRF handling in ApiRunnerMixin."""

from unittest.mock import MagicMock, patch
import http.cookiejar
from testql.interpreter.interpreter import OqlInterpreter


def test_should_use_insecure_ssl_hostnames():
    interp = OqlInterpreter()
    assert interp._should_use_insecure_ssl("https://app.clonerd.com.local/healthz") is True
    assert interp._should_use_insecure_ssl("https://mysite.local/api") is True
    assert interp._should_use_insecure_ssl("http://localhost:8891/healthz") is True
    assert interp._should_use_insecure_ssl("https://127.0.0.1:8891/healthz") is True
    assert interp._should_use_insecure_ssl("https://example.com/api") is False


def test_should_use_insecure_ssl_env_or_config(monkeypatch):
    interp = OqlInterpreter()
    monkeypatch.setenv("TESTQL_INSECURE", "1")
    assert interp._should_use_insecure_ssl("https://example.com/api") is True

    monkeypatch.delenv("TESTQL_INSECURE")
    interp.config = {"insecure": True}
    assert interp._should_use_insecure_ssl("https://example.com/api") is True


def test_cookie_jar_persists_across_calls():
    interp = OqlInterpreter()
    jar = interp._get_cookie_jar()
    assert isinstance(jar, http.cookiejar.CookieJar)
    # Consecutive calls return the exact same instance
    assert interp._get_cookie_jar() is jar


def test_csrf_token_auto_injection():
    interp = OqlInterpreter()
    interp.vars.set("csrf", "test-token-12345")
    mock_opener = MagicMock()
    mock_resp = MagicMock()
    mock_resp.status = 200
    mock_resp.headers = {"content-type": "application/json"}
    mock_resp.read.return_value = b'{"ok": true}'
    mock_opener.open.return_value.__enter__.return_value = mock_resp

    with patch.object(interp, "_get_opener", return_value=mock_opener):
        status, data, headers, evidence = interp._do_http_request("POST", "http://localhost:8891/test", {"a": 1})
        assert status == 200
        req = mock_opener.open.call_args[0][0]
        assert req.headers.get("X-csrf-token") == "test-token-12345"
