# ABOUTME: End-to-end check that every remote install artifact the labs fetch still resolves.
# ABOUTME: Needs outbound HTTPS; fails with a clear message when the network is unreachable.

import re
import urllib.error
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


def _get(url: str, accept: str | None = None) -> int:
    """GET the first byte of `url`, following redirects, and return the final status code."""
    headers = {"User-Agent": USER_AGENT, "Range": "bytes=0-0"}
    if accept:
        headers["Accept"] = accept
    request = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(request, timeout=TIMEOUT_SECONDS) as response:
            return int(response.status)
    except urllib.error.HTTPError as err:
        return err.code


@pytest.fixture(scope="session", autouse=True)
def network() -> None:
    """Fail every test up front, with one clear reason, when there is no outbound HTTPS."""
    try:
        _get("https://github.com")
    except (urllib.error.URLError, TimeoutError, OSError) as err:
        pytest.fail(
            "The E2E suite needs outbound HTTPS to reach the URLs the labs install from, "
            f"and https://github.com is unreachable: {err}",
            pytrace=False,
        )


def test_sources_reference_install_urls() -> None:
    """Guard the extractor: if it finds nothing, the parametrized checks below prove nothing."""
    assert len(FETCHES) >= 10, f"Expected at least 10 fetched URLs, found {sorted(FETCHES)}"
    assert HELM_REPOS, "Expected at least one `helm repo add` URL"
    assert OCI_CHARTS, "Expected at least one `helm install oci://... --version` chart"


@pytest.mark.parametrize("url", sorted(FETCHES))
def test_fetched_url_resolves(url: str) -> None:
    """Every URL a lab tells the learner to `kubectl apply -f`, curl, or clone must resolve."""
    status = _get(url)
    assert status in (200, 206), (
        f"HTTP {status} for {url}\nReferenced at: {', '.join(FETCHES[url])}"
    )


@pytest.mark.parametrize("url", sorted(HELM_REPOS))
def test_helm_repo_index_resolves(url: str) -> None:
    """Every `helm repo add` URL must serve an index.yaml, or `helm repo add` fails."""
    status = _get(url)
    assert status in (200, 206), (
        f"HTTP {status} for {url}\nReferenced at: {', '.join(HELM_REPOS[url])}"
    )


@pytest.mark.parametrize("url", sorted(OCI_CHARTS))
def test_oci_chart_version_exists(url: str) -> None:
    """Every pinned `helm install oci://... --version X` must name a tag the registry serves."""
    status = _get(url, accept=OCI_MANIFEST_TYPES)
    assert status in (200, 206), (
        f"HTTP {status} for {url}\nReferenced at: {', '.join(OCI_CHARTS[url])}"
    )
