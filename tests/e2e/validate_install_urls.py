# ABOUTME: End-to-end check that every remote install artifact the labs fetch still resolves.
# ABOUTME: Needs outbound HTTPS; fails with a clear message when the network is unreachable.

import json
import re
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

import pytest

from tests.conftest import EXCLUDED_PATTERNS

REPO_ROOT = Path(__file__).parent.parent.parent

# What a learner reads and runs: the lab READMEs and scripts, the contributor test script, and
# the top-level entry points.
SOURCE_GLOBS = ["labs/**/*.md", "labs/**/*.sh", "scripts/*.sh", "README.md", "checklist.md"]

# A literal URL ends at whitespace, a quote, a closing paren or bracket, or a backtick.
URL = r"https://[^\s\"'`)<>\]]+"
URL_PATTERN = re.compile(URL)

# A line running one of these downloads every https URL on it. Collecting all of them, not just
# the first, catches nested fetches such as kubectl's `curl .../$(curl .../stable.txt)/...`.
FETCH_COMMAND = re.compile(
    r"\b(?:kubectl\s+(?:apply|create)\b[^\n]*?-f\s|curl\b|wget\b|git\s+clone\b)"
)
HELM_REPO_ADD = re.compile(r"\bhelm\s+repo\s+add\s+\S+\s+(" + URL + ")")
HELM_OCI_INSTALL = re.compile(
    r"\bhelm\s+(?:install|upgrade)\b[^\n]*?oci://([^/\s]+)/(\S+?)\s[^\n]*?--version[\s=]+(\S+)"
)

OCI_MANIFEST_TYPES = (
    "application/vnd.oci.image.manifest.v1+json, application/vnd.oci.image.index.v1+json"
)
TIMEOUT_SECONDS = 30
USER_AGENT = "cloud-native-ai-lab-e2e (+https://github.com/peopleforrester/cloud-native-ai-lab)"


def _logical_lines(text: str) -> list[tuple[int, str]]:
    """Join backslash-continued shell lines so a multi-line command reads as one.

    Returns (first line number, joined text) pairs. Markdown blockquote markers are dropped,
    since a lab may quote an alternative install command inside a "> **Note:**" block.
    """
    logical: list[tuple[int, str]] = []
    start = 0
    parts: list[str] = []
    for lineno, raw in enumerate(text.splitlines(), start=1):
        line = re.sub(r"^\s*>\s?", "", raw)
        if not parts:
            start = lineno
        if line.rstrip().endswith("\\"):
            parts.append(line.rstrip()[:-1])
            continue
        parts.append(line)
        logical.append((start, " ".join(parts)))
        parts = []
    if parts:
        logical.append((start, " ".join(parts)))
    return logical


def _source_files() -> list[Path]:
    files: set[Path] = set()
    for pattern in SOURCE_GLOBS:
        for path in REPO_ROOT.glob(pattern):
            rel = str(path.relative_to(REPO_ROOT))
            if not any(excluded in rel for excluded in EXCLUDED_PATTERNS):
                files.add(path)
    return sorted(files)


def _collect() -> tuple[dict[str, list[str]], dict[str, list[str]], dict[str, list[str]]]:
    """Return {url: [where it appears]} for direct fetches, Helm repos, and OCI chart manifests."""
    fetches: dict[str, list[str]] = {}
    helm_repos: dict[str, list[str]] = {}
    oci_charts: dict[str, list[str]] = {}
    for path in _source_files():
        rel = str(path.relative_to(REPO_ROOT))
        for lineno, line in _logical_lines(path.read_text()):
            where = f"{rel}:{lineno}"
            if FETCH_COMMAND.search(line):
                for url in URL_PATTERN.findall(line):
                    # `$(...)` or `${...}` means the shell builds the URL at run time; the inner
                    # literal URL (for example stable.txt) is collected on its own.
                    if "$" not in url:
                        fetches.setdefault(url, []).append(where)
            for url in HELM_REPO_ADD.findall(line):
                helm_repos.setdefault(url.rstrip("/") + "/index.yaml", []).append(where)
            for host, chart, version in HELM_OCI_INSTALL.findall(line):
                manifest = f"https://{host}/v2/{chart}/manifests/{version}"
                oci_charts.setdefault(manifest, []).append(where)
    return fetches, helm_repos, oci_charts


FETCHES, HELM_REPOS, OCI_CHARTS = _collect()


def _get(url: str, accept: str | None = None, token: str | None = None) -> tuple[int, str]:
    """GET the first byte of `url`, following redirects.

    Returns the final status code and its WWW-Authenticate header ("" when absent).
    """
    headers = {"User-Agent": USER_AGENT, "Range": "bytes=0-0"}
    if accept:
        headers["Accept"] = accept
    if token:
        headers["Authorization"] = f"Bearer {token}"
    request = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(request, timeout=TIMEOUT_SECONDS) as response:
            return int(response.status), ""
    except urllib.error.HTTPError as err:
        return err.code, err.headers.get("WWW-Authenticate", "")


def _bearer_challenge(header: str) -> dict[str, str]:
    """Parse `Bearer realm="...",service="...",scope="..."` into its parameters.

    Returns {} when the header is not a Bearer challenge or names no realm.
    """
    scheme, _, params = header.strip().partition(" ")
    if scheme.lower() != "bearer":
        return {}
    challenge = dict(re.findall(r'(\w+)="([^"]*)"', params))
    return challenge if challenge.get("realm") else {}


def _anonymous_token(challenge: dict[str, str]) -> str:
    """Fetch a pull token from the challenge's realm, as `helm pull` does for a public chart."""
    realm = challenge["realm"]
    assert realm.startswith("https://"), f"Registry token realm is not HTTPS: {realm}"
    params: dict[str, str] = {
        key: challenge[key] for key in ("service", "scope") if key in challenge
    }
    query = urllib.parse.urlencode(params)
    request = urllib.request.Request(
        f"{realm}?{query}" if query else realm, headers={"User-Agent": USER_AGENT}
    )
    with urllib.request.urlopen(request, timeout=TIMEOUT_SECONDS) as response:
        body = json.load(response)
    # The distribution token spec names the field `token`; OAuth2-style realms use `access_token`.
    token = body.get("token") or body.get("access_token")
    assert token, f"Token realm {realm} returned no token for {query}"
    return str(token)


def _get_oci_manifest(url: str) -> int:
    """GET an OCI manifest, answering a registry's Bearer challenge with an anonymous token.

    ghcr.io returns 401 to any manifest request without a token, even for public charts.
    On a 401 carrying a Bearer challenge this fetches an anonymous token and retries once.
    """
    status, authenticate = _get(url, accept=OCI_MANIFEST_TYPES)
    challenge = _bearer_challenge(authenticate) if status == 401 else {}
    if not challenge:
        return status
    status, _ = _get(url, accept=OCI_MANIFEST_TYPES, token=_anonymous_token(challenge))
    return status


def test_sources_reference_install_urls() -> None:
    """Guard the extractor: if it finds nothing, the parametrized checks below prove nothing."""
    assert len(FETCHES) >= 10, f"Expected at least 10 fetched URLs, found {sorted(FETCHES)}"
    assert HELM_REPOS, "Expected at least one `helm repo add` URL"
    assert OCI_CHARTS, "Expected at least one `helm install oci://... --version` chart"


@pytest.mark.parametrize("url", sorted(FETCHES))
def test_fetched_url_resolves(url: str) -> None:
    """Every URL a lab tells the learner to `kubectl apply -f`, curl, or clone must resolve."""
    status, _ = _get(url)
    assert status in (200, 206), (
        f"HTTP {status} for {url}\nReferenced at: {', '.join(FETCHES[url])}"
    )


@pytest.mark.parametrize("url", sorted(HELM_REPOS))
def test_helm_repo_index_resolves(url: str) -> None:
    """Every `helm repo add` URL must serve an index.yaml, or `helm repo add` fails."""
    status, _ = _get(url)
    assert status in (200, 206), (
        f"HTTP {status} for {url}\nReferenced at: {', '.join(HELM_REPOS[url])}"
    )


@pytest.mark.parametrize("url", sorted(OCI_CHARTS))
def test_oci_chart_version_exists(url: str) -> None:
    """Every pinned `helm install oci://... --version X` must name a tag the registry serves."""
    status = _get_oci_manifest(url)
    assert status in (200, 206), (
        f"HTTP {status} for {url}\nReferenced at: {', '.join(OCI_CHARTS[url])}"
    )
