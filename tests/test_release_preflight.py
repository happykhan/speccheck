import urllib.error

from scripts import release_preflight


def test_github_release_state_reports_http_errors(monkeypatch):
    def fail_fetch(_url):
        raise urllib.error.HTTPError(
            url="https://api.github.com/example",
            code=403,
            msg="rate limit exceeded",
            hdrs=None,
            fp=None,
        )

    monkeypatch.setattr(release_preflight, "fetch_json", fail_fetch)

    checks = release_preflight.github_release_state("1.3.0")

    assert len(checks) == 1
    assert checks[0].label == "GitHub release API"
    assert not checks[0].ok
    assert "HTTP 403" in checks[0].detail


def test_fetch_json_uses_github_token_for_github_api(monkeypatch):
    captured = {}

    class Response:
        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return None

        def read(self):
            return b"{}"

    def fake_urlopen(request, timeout):
        captured["authorization"] = request.headers.get("Authorization")
        captured["timeout"] = timeout
        return Response()

    monkeypatch.setenv("GITHUB_TOKEN", "token-value")
    monkeypatch.setattr(release_preflight.urllib.request, "urlopen", fake_urlopen)

    assert release_preflight.fetch_json("https://api.github.com/repos/happykhan/speccheck") == {}
    assert captured == {"authorization": "Bearer token-value", "timeout": 20}
