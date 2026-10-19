# ABOUTME: End-to-end check of lab 06's manifests against the CRDs in the kagent-crds chart it pins.
# ABOUTME: Pulls the chart from its OCI registry, reads its CRD schemas, validates every manifest.

import hashlib
import json
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any

import pytest
import yaml

from tests.e2e.crd_schema import CRDVersion, chart_crds, validate_object
from tests.e2e.validate_install_urls import (
    HELM_OCI_INSTALL,
    OCI_MANIFEST_TYPES,
    TIMEOUT_SECONDS,
    USER_AGENT,
    _anonymous_token,
    _bearer_challenge,
    _get,
    _logical_lines,
)

REPO_ROOT = Path(__file__).parent.parent.parent
LAB = REPO_ROOT / "labs" / "06-kagent-mcp"
CHART_NAME = "kagent-crds"
HELM_CHART_LAYER = "application/vnd.cncf.helm.chart.content.v1.tar+gzip"
# Kinds the API server serves itself, so no chart CRD describes them.
CORE_KINDS = {("v1", "Namespace")}


def _pins() -> list[tuple[str, str, str, str]]:
    """Return (host, repository, version, the install line) for each kagent-crds install."""
    readme = LAB / "README.md"
    pins = []
    for lineno, line in _logical_lines(readme.read_text()):
        for host, repository, version in HELM_OCI_INSTALL.findall(line):
            if repository.rsplit("/", 1)[-1] == CHART_NAME:
                pins.append((host, repository, version, f"{readme.name}:{lineno}: {line.strip()}"))
    return pins


def _documents() -> dict[str, dict[str, Any]]:
    """Every YAML document in lab 06's manifests, keyed `file#index`."""
    docs: dict[str, dict[str, Any]] = {}
    for path in sorted((LAB / "manifests").glob("*.yaml")):
        for index, doc in enumerate(yaml.safe_load_all(path.read_text())):
            if doc:
                docs[f"{path.name}#{index}"] = doc
    return docs


PINS = _pins()
DOCUMENTS = _documents()
CUSTOM_RESOURCES = sorted(
    name for name, doc in DOCUMENTS.items() if "/" in str(doc.get("apiVersion", ""))
)

# What lab 06 shipped before #12, cut down to the fields kagent never served. Each must fail
# against the real schema, which shows the check rejects unknown fields rather than passing all.
PRE_12_MANIFESTS = {
    "agent": """
apiVersion: kagent.dev/v1alpha1
kind: Agent
metadata: {name: k8s-helper, namespace: agents}
spec:
  description: A Kubernetes helper agent.
  model: {provider: openai, name: gpt-4o, apiEndpoint: "https://api.openai.com/v1"}
  systemPrompt: You are a Kubernetes cluster assistant.
  mcpServers: [{name: kubernetes-tools}]
""",
    "mcp-server": """
apiVersion: kagent.dev/v1alpha1
kind: MCPServer
metadata: {name: kubernetes-tools, namespace: agents}
spec:
  transport: stdio
  image: ghcr.io/kagent-dev/kagent/tools:0.2.1
  args: ["--transport=stdio"]
  tools: [{name: get_pods, description: List pods in a namespace}]
""",
}


class _DropAuthOnHostChange(urllib.request.HTTPRedirectHandler):
    """Follow redirects, but keep the registry token away from the blob storage host."""

    def redirect_request(
        self,
        req: urllib.request.Request,
        fp: Any,
        code: int,
        msg: str,
        headers: Any,
        newurl: str,
    ) -> urllib.request.Request | None:
        new = super().redirect_request(req, fp, code, msg, headers, newurl)
        if new is not None and urllib.parse.urlsplit(newurl).netloc != req.host:
            new.remove_header("Authorization")
        return new


_OPENER = urllib.request.build_opener(_DropAuthOnHostChange)


def _fetch(url: str, token: str, accept: str | None = None) -> bytes:
    headers = {"User-Agent": USER_AGENT, "Authorization": f"Bearer {token}"}
    if accept:
        headers["Accept"] = accept
    request = urllib.request.Request(url, headers=headers)
    try:
        with _OPENER.open(request, timeout=TIMEOUT_SECONDS) as response:
            return bytes(response.read())
    except urllib.error.HTTPError as err:
        raise AssertionError(f"HTTP {err.code} for {url}") from err


def _pull_chart(host: str, repository: str, version: str) -> bytes:
    """Pull a chart as `helm pull` does: anonymous token, then manifest, then the chart layer."""
    manifest_url = f"https://{host}/v2/{repository}/manifests/{version}"
    status, authenticate = _get(manifest_url, accept=OCI_MANIFEST_TYPES)
    challenge = _bearer_challenge(authenticate)
    assert status == 401 and challenge, (
        f"Expected {host} to answer an anonymous manifest request with a Bearer challenge, "
        f"got HTTP {status} with WWW-Authenticate {authenticate!r}"
    )
    token = _anonymous_token(challenge)
    manifest = json.loads(_fetch(manifest_url, token, accept=OCI_MANIFEST_TYPES))
    layers = [
        layer for layer in manifest.get("layers", []) if layer["mediaType"] == HELM_CHART_LAYER
    ]
    assert len(layers) == 1, f"{manifest_url} has no single {HELM_CHART_LAYER} layer: {manifest}"
    digest = layers[0]["digest"]
    algorithm, _, expected = digest.partition(":")
    assert algorithm == "sha256", f"Unexpected digest algorithm in {digest}"
    blob = _fetch(f"https://{host}/v2/{repository}/blobs/{digest}", token)
    actual = hashlib.sha256(blob).hexdigest()
    assert actual == expected, f"Chart layer digest is sha256:{actual}, manifest says {digest}"
    assert len(blob) == layers[0]["size"], f"Chart layer is {len(blob)} bytes, manifest says more"
    return blob


@pytest.fixture(scope="module")
def crds() -> dict[tuple[str, str], CRDVersion]:
    """The CRDs a default `helm install` of lab 06's pinned kagent-crds chart applies."""
    assert len(PINS) == 1, f"Expected one pinned kagent-crds install in lab 06, found {PINS}"
    host, repository, version, _ = PINS[0]
    return chart_crds(_pull_chart(host, repository, version))


def test_readme_pins_one_default_install() -> None:
    """Guard the extractor, and that the install uses chart defaults, which is what is checked."""
    assert len(PINS) == 1, f"Expected one `helm install ... {CHART_NAME} --version` line: {PINS}"
    line = PINS[0][3]
    assert not any(flag in line.split() for flag in ("--set", "-f", "--values")), (
        f"The install overrides chart values, so the default CRD set may not be the one used: {line}"
    )
    assert len(CUSTOM_RESOURCES) >= 3, f"Expected lab 06's kagent manifests, found {DOCUMENTS}"


def test_other_manifests_are_core_kinds() -> None:
    """A manifest outside every API group must be a core kind, since no CRD can describe it."""
    other = {
        name: (doc.get("apiVersion"), doc.get("kind"))
        for name, doc in DOCUMENTS.items()
        if name not in CUSTOM_RESOURCES
    }
    unexpected = {name: key for name, key in other.items() if key not in CORE_KINDS}
    assert not unexpected, f"Lab 06 manifests of kinds this check cannot validate: {unexpected}"


@pytest.mark.parametrize("name", CUSTOM_RESOURCES)
def test_manifest_matches_chart_schema(name: str, crds: dict[tuple[str, str], CRDVersion]) -> None:
    """Each custom resource is a kind the chart serves, and its CRD schema accepts it."""
    doc = DOCUMENTS[name]
    key = (str(doc.get("apiVersion")), str(doc.get("kind")))
    assert key in crds, f"{name}: the pinned chart has no CRD for {key}. Served: {sorted(crds)}"
    crd = crds[key]
    errors = validate_object(crd, doc)
    assert not errors, f"{name} breaks {crd.source} ({key[0]} {key[1]}):\n" + "\n".join(errors)


@pytest.mark.parametrize("name", CUSTOM_RESOURCES)
def test_unknown_spec_field_is_rejected(name: str, crds: dict[tuple[str, str], CRDVersion]) -> None:
    """The real schema closes `spec`, so a field it does not declare is reported."""
    doc = DOCUMENTS[name]
    crd = crds[(str(doc.get("apiVersion")), str(doc.get("kind")))]
    mutated = {**doc, "spec": {**doc.get("spec", {}), "notAKagentField": True}}
    assert ".spec.notAKagentField: unknown field" in validate_object(crd, mutated)


@pytest.mark.parametrize("label", sorted(PRE_12_MANIFESTS))
def test_pre_12_manifest_is_rejected(label: str, crds: dict[tuple[str, str], CRDVersion]) -> None:
    """The fields lab 06 used before #12 were never in any kagent CRD, and fail here."""
    doc = yaml.safe_load(PRE_12_MANIFESTS[label])
    crd = crds[(doc["apiVersion"], doc["kind"])]
    unknown = [error for error in validate_object(crd, doc) if error.endswith("unknown field")]
    assert unknown, f"The pre-#12 {label} manifest passed validation against {crd.source}"
