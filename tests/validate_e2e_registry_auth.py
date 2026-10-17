# ABOUTME: Offline checks of the E2E suite's OCI registry auth: Bearer challenge parsing and retry.
# ABOUTME: Replaces the HTTP calls with stubs, so it runs in the Test command without the network.

import pytest

from tests.e2e import validate_install_urls as urls

GHCR_MANIFEST = "https://ghcr.io/v2/kagent-dev/kagent/helm/kagent-crds/manifests/0.10.3"
GHCR_CHALLENGE = (
    'Bearer realm="https://ghcr.io/token",service="ghcr.io",'
    'scope="repository:kagent-dev/kagent/helm/kagent-crds:pull"'
)


class TestBearerChallenge:
    def test_parses_ghcr_challenge(self) -> None:
        assert urls._bearer_challenge(GHCR_CHALLENGE) == {
            "realm": "https://ghcr.io/token",
            "service": "ghcr.io",
            "scope": "repository:kagent-dev/kagent/helm/kagent-crds:pull",
        }

    def test_scheme_is_case_insensitive(self) -> None:
        assert urls._bearer_challenge('bearer realm="https://r.example/token"') == {
            "realm": "https://r.example/token"
        }

    @pytest.mark.parametrize(
        "header",
        ["", 'Basic realm="registry"', 'Bearer service="ghcr.io"'],
    )
    def test_rejects_non_bearer_or_realmless(self, header: str) -> None:
        assert urls._bearer_challenge(header) == {}


class TestOciManifestRetry:
    def _stub(
        self, monkeypatch: pytest.MonkeyPatch, responses: list[tuple[int, str]]
    ) -> tuple[list[str | None], list[dict[str, str]]]:
        """Serve `responses` in order from _get; record the tokens sent and challenges answered."""
        sent: list[str | None] = []
        answered: list[dict[str, str]] = []

        def fake_get(
            url: str, accept: str | None = None, token: str | None = None
        ) -> tuple[int, str]:
            assert url == GHCR_MANIFEST
            assert accept == urls.OCI_MANIFEST_TYPES
            sent.append(token)
            return responses.pop(0)

        def fake_token(challenge: dict[str, str]) -> str:
            answered.append(challenge)
            return "anon-token"

        monkeypatch.setattr(urls, "_get", fake_get)
        monkeypatch.setattr(urls, "_anonymous_token", fake_token)
        return sent, answered

    def test_401_with_challenge_retries_once_with_token(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        sent, answered = self._stub(monkeypatch, [(401, GHCR_CHALLENGE), (200, "")])
        assert urls._get_oci_manifest(GHCR_MANIFEST) == 200
        assert sent == [None, "anon-token"]
        assert answered == [urls._bearer_challenge(GHCR_CHALLENGE)]

    def test_second_401_is_reported_not_retried_again(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        sent, _ = self._stub(monkeypatch, [(401, GHCR_CHALLENGE), (401, GHCR_CHALLENGE)])
        assert urls._get_oci_manifest(GHCR_MANIFEST) == 401
        assert sent == [None, "anon-token"]

    def test_missing_tag_after_token_is_reported(self, monkeypatch: pytest.MonkeyPatch) -> None:
        self._stub(monkeypatch, [(401, GHCR_CHALLENGE), (404, "")])
        assert urls._get_oci_manifest(GHCR_MANIFEST) == 404

    @pytest.mark.parametrize("response", [(200, ""), (404, ""), (401, 'Basic realm="x"')])
    def test_no_token_without_bearer_401(
        self, monkeypatch: pytest.MonkeyPatch, response: tuple[int, str]
    ) -> None:
        sent, answered = self._stub(monkeypatch, [response])
        assert urls._get_oci_manifest(GHCR_MANIFEST) == response[0]
        assert sent == [None]
        assert answered == []


def test_token_realm_must_be_https() -> None:
    with pytest.raises(AssertionError, match="not HTTPS"):
        urls._anonymous_token({"realm": "http://ghcr.io/token"})
