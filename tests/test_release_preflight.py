import urllib.error

from scripts import release_preflight


def test_github_release_state_falls_back_after_http_errors(monkeypatch):
    def fail_fetch(_url):
        raise urllib.error.HTTPError(
            url="https://api.github.com/example",
            code=403,
            msg="rate limit exceeded",
            hdrs=None,
            fp=None,
        )

    def fake_run(*_args, **_kwargs):
        class Result:
            stdout = ""

        return Result()

    monkeypatch.setattr(release_preflight, "fetch_json", fail_fetch)
    monkeypatch.setattr(release_preflight.subprocess, "run", fake_run)
    monkeypatch.setattr(
        release_preflight,
        "url_status",
        lambda _url: (_ for _ in ()).throw(
            urllib.error.HTTPError(
                url="https://github.com/example",
                code=404,
                msg="Not Found",
                hdrs=None,
                fp=None,
            )
        ),
    )

    checks = release_preflight.github_release_state("1.3.0")

    assert len(checks) == 3
    assert checks[0].label == "GitHub release API"
    assert checks[0].ok
    assert checks[0].warning
    assert checks[1].detail == "v1.3.0 is available"
    assert checks[2].detail == "release v1.3.0 is available"


def test_github_release_state_fallback_blocks_existing_tag(monkeypatch):
    def fake_run(*_args, **_kwargs):
        class Result:
            stdout = "abc123\trefs/tags/v1.3.0\n"

        return Result()

    monkeypatch.setattr(release_preflight.subprocess, "run", fake_run)
    monkeypatch.setattr(release_preflight, "url_status", lambda _url: 200)

    checks = release_preflight.github_release_state_fallback("v1.3.0")

    assert not checks[0].ok
    assert checks[0].detail == "v1.3.0 already exists"
    assert not checks[1].ok
    assert checks[1].detail == "release v1.3.0 already exists"


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
