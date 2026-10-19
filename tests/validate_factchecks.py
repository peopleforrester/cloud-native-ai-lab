# ABOUTME: Validates that the 5 mandatory fact-check corrections are applied across all docs.
# ABOUTME: Checks for incorrect values and ensures correct values appear at least once.

import re
from pathlib import Path
from typing import Any, ClassVar

import pytest
import yaml

EXCLUDED_DIRS = ["claude-ai-context", "transcripts", "node_modules", "__pycache__", ".git/"]


def _read_content_files(repo_root: Path) -> list[tuple[Path, str]]:
    """Read all final content markdown files (excluding source originals and tests)."""
    # Local-only directories (claude-ai-context/, transcripts/) are gitignored and
    # never published: the archive intentionally preserves pre-correction source
    # facts, and transcripts may carry third-party personal information.
    excluded_patterns = [
        "compass_artifact",
        "claude-ai-context",
        "transcripts",
        "node_modules",
        "__pycache__",
        ".git/",
    ]
    results = []
    for md_file in repo_root.rglob("*.md"):
        rel = str(md_file.relative_to(repo_root))
        if not any(pattern in rel for pattern in excluded_patterns):
            results.append((md_file, md_file.read_text()))
    return results


class TestJobSetVersion:
    """JobSet version must be v0.12.0, not the older v0.10.1."""

    def test_no_incorrect_jobset_version(self, repo_root: Path) -> None:
        """The incorrect JobSet version v0.10.1 should not appear as a current version."""
        for md_file, content in _read_content_files(repo_root):
            if "v0.10.1" not in content or "jobset" not in content.lower():
                continue
            # Allow in correction context (e.g., "NOT v0.10.1")
            for line in content.split("\n"):
                if "v0.10.1" in line:
                    lower_line = line.lower()
                    correction_context = any(
                        word in lower_line
                        for word in [
                            "not v0.10.1",
                            "incorrect",
                            "corrected",
                            "should be",
                            "was v0.10.1",
                        ]
                    )
                    if not correction_context:
                        rel = md_file.relative_to(repo_root)
                        pytest.fail(
                            f"{rel} contains incorrect JobSet version v0.10.1 (should be v0.12.0)"
                        )

    def test_correct_jobset_version_exists(self, repo_root: Path) -> None:
        """The correct JobSet version v0.12.0 must appear in at least one content file."""
        for _, content in _read_content_files(repo_root):
            if "v0.12.0" in content:
                return
        pytest.fail("Correct JobSet version v0.12.0 not found in any content file")


class TestMCPServerCount:
    """MCP server count must be 10,000+, not 6,400."""

    def test_no_incorrect_mcp_count(self, repo_root: Path) -> None:
        """The incorrect MCP server count 6,400 should not appear as a current count."""
        for md_file, content in _read_content_files(repo_root):
            if "6,400" not in content and "6400" not in content:
                continue
            for line in content.split("\n"):
                if "6,400" in line or "6400" in line:
                    lower_line = line.lower()
                    correction_context = any(
                        word in lower_line
                        for word in ["not 6,400", "not 6400", "incorrect", "corrected", "should be"]
                    )
                    if not correction_context:
                        rel = md_file.relative_to(repo_root)
                        pytest.fail(
                            f"{rel} contains incorrect MCP server count 6,400 (should be 10,000+)"
                        )

    def test_correct_mcp_count_exists(self, repo_root: Path) -> None:
        """The correct MCP server count 10,000+ must appear in at least one content file."""
        for _, content in _read_content_files(repo_root):
            if "10,000" in content or "10000" in content:
                return
        pytest.fail("Correct MCP server count 10,000+ not found in any content file")


class TestInferenceObjective:
    """InferenceModel was renamed to InferenceObjective in GA/v1."""

    def test_no_inferencemodel_in_ga_context(self, repo_root: Path) -> None:
        """InferenceModel should not appear as a current GA CRD name.

        Note: It's acceptable to mention InferenceModel in historical context
        (e.g., 'renamed from InferenceModel'), so we check for patterns that
        present it as the current name.
        """
        for md_file, content in _read_content_files(repo_root):
            rel = str(md_file.relative_to(repo_root))
            # Skip the fact-check source document itself
            if "compass_artifact" in rel:
                continue
            # Check for InferenceModel used as a current CRD name
            # Allow mentions in historical/rename context
            lines = content.split("\n")
            for i, line in enumerate(lines, 1):
                if "InferenceModel" in line:
                    # Check surrounding context (3 lines before and after)
                    start = max(0, i - 4)
                    end = min(len(lines), i + 3)
                    context_block = " ".join(lines[start:end]).lower()
                    rename_context = any(
                        word in context_block
                        for word in [
                            "renamed",
                            "was renamed",
                            "previously",
                            "formerly",
                            "migration",
                            "replaced",
                            "old name",
                            "not inferencemodel",
                            "pre-ga",
                            "pre_ga",
                        ]
                    )
                    if not rename_context:
                        pytest.fail(
                            f"{rel}:{i} uses 'InferenceModel' as current CRD name "
                            f"(should be 'InferenceObjective' for GA/v1)"
                        )

    def test_correct_inference_objective_exists(self, repo_root: Path) -> None:
        """InferenceObjective must appear in at least one content file."""
        for _, content in _read_content_files(repo_root):
            if "InferenceObjective" in content:
                return
        pytest.fail("InferenceObjective not found in any content file")

    def test_inference_objective_uses_llm_d_group(self, repo_root: Path) -> None:
        """Any manifest declaring kind InferenceObjective must use the llm-d group.

        InferenceObjective was never served by the Gateway API Inference
        Extension GA group. It lived at inference.networking.x-k8s.io/v1alpha2
        from GAIE v1.0.0 through v1.5.0, was removed in v1.6.0, and now lives in
        llm-d-router at llm-d.ai/v1alpha2. A manifest claiming it under
        inference.networking.k8s.io/v1 has never been appliable against any
        release, which is exactly the error this gate exists to catch.
        """
        bad: list[str] = []
        for yaml_file in repo_root.rglob("*.yaml"):
            rel = str(yaml_file.relative_to(repo_root))
            if any(skip in rel for skip in EXCLUDED_DIRS):
                continue
            text = yaml_file.read_text()
            if "kind: InferenceObjective" not in text:
                continue
            if "apiVersion: llm-d.ai/v1alpha2" not in text:
                declared = next(
                    (ln.strip() for ln in text.splitlines() if ln.startswith("apiVersion:")),
                    "(none)",
                )
                bad.append(f"{rel}: declares {declared}, expected apiVersion: llm-d.ai/v1alpha2")
        assert not bad, "InferenceObjective must use llm-d.ai/v1alpha2:\n" + "\n".join(bad)

    def test_inference_pool_stays_on_ga_group(self, repo_root: Path) -> None:
        """InferencePool is the kind that actually went GA, and stays there."""
        pool = repo_root / "labs" / "05-gateway-routing" / "manifests" / "inference-pool.yaml"
        text = pool.read_text()
        assert "apiVersion: inference.networking.k8s.io/v1" in text, (
            "InferencePool must remain on the GA group inference.networking.k8s.io/v1"
        )


class TestGenAIStatQualifier:
    """The 66% gen AI stat must include its qualifier wherever it appears."""

    def test_66_percent_has_qualifier(self, repo_root: Path) -> None:
        """When 66% appears with gen AI context, it should have the qualifier."""
        for md_file, content in _read_content_files(repo_root):
            rel = str(md_file.relative_to(repo_root))
            # Skip source materials (fact-check doc and talk outline)
            if "compass_artifact" in rel or "talk-outline" in rel:
                continue
            # Look for "66%" near gen AI / generative AI context
            matches = list(re.finditer(r"66\s*%", content))
            for match in matches:
                # Get surrounding context (200 chars each direction)
                start = max(0, match.start() - 200)
                end = min(len(content), match.end() + 200)
                context = content[start:end].lower()
                if any(term in context for term in ["generative ai", "gen ai", "genai"]):
                    # Check for qualifier
                    has_qualifier = any(
                        phrase in context
                        for phrase in [
                            "hosting generative ai models",
                            "host generative ai models",
                            "organizations already hosting",
                            "organizations that host",
                            "orgs hosting",
                        ]
                    )
                    if not has_qualifier:
                        pytest.fail(
                            f"{rel} uses 66% gen AI stat without qualifier. "
                            f"Must specify 'of organizations already hosting "
                            f"generative AI models'"
                        )


class TestDeclarativeNamespaces:
    """Lab READMEs should use declarative `kubectl apply -f` for namespaces,
    matching the rest of each lab's manifest-driven style."""

    def test_no_imperative_namespace_creation(self, repo_root: Path) -> None:
        """`kubectl create namespace` is forbidden in main lab READMEs."""
        forbidden_files = [
            repo_root / "labs" / "01-kueue-basics" / "README.md",
            repo_root / "labs" / "04-kserve-inference" / "README.md",
            repo_root / "labs" / "06-kagent-mcp" / "README.md",
        ]
        bad: list[str] = []
        # Normalize whitespace and case so command variants ("kubectl  create
        # Namespace", extra spaces) cannot slip past the gate.
        imperative = re.compile(r"kubectl\s+create\s+namespace", re.IGNORECASE)
        for path in forbidden_files:
            content = path.read_text()
            for i, line in enumerate(content.split("\n"), 1):
                if imperative.search(line):
                    rel = path.relative_to(repo_root)
                    bad.append(f"{rel}:{i}: {line.strip()}")
        assert not bad, (
            "Use `kubectl apply -f` for namespaces, not imperative create:\n" + "\n".join(bad)
        )


class TestDRADriverPath:
    """Lab 02 Part B must reference the canonical kubernetes-sigs/dra-example-driver,
    not the non-existent kubernetes/test/e2e/dra/test-driver path."""

    def test_no_stale_dra_test_driver_path(self, repo_root: Path) -> None:
        """`kubernetes/test/e2e/dra/test-driver` must not appear in any final content."""
        for md_file, content in _read_content_files(repo_root):
            rel = str(md_file.relative_to(repo_root))
            if "compass_artifact" in rel or "improvement-plan" in rel:
                continue
            for i, line in enumerate(content.split("\n"), 1):
                if "kubernetes/test/e2e/dra/test-driver" in line:
                    pytest.fail(
                        f"{rel}:{i} references the non-existent "
                        f"`kubernetes/test/e2e/dra/test-driver` path. "
                        f"Use `kubernetes-sigs/dra-example-driver` instead."
                    )

    def test_dra_lab_uses_kubernetes_sigs_repo(self, repo_root: Path) -> None:
        """Lab 02 README must point at github.com/kubernetes-sigs/dra-example-driver."""
        lab_readme = repo_root / "labs" / "02-dra-resource-claims" / "README.md"
        content = lab_readme.read_text()
        assert "kubernetes-sigs/dra-example-driver" in content, (
            "Lab 02 README must reference the canonical kubernetes-sigs/dra-example-driver repo"
        )


class TestKServeVersion:
    """Lab 04 must offer KServe v0.20.0 with --server-side as the recommended path."""

    def test_kserve_lab_recommends_v020_server_side(self, repo_root: Path) -> None:
        """Lab 04 README must offer a working `kubectl apply --server-side` command
        that installs KServe v0.20.0, not just mention it in prose."""
        lab_readme = repo_root / "labs" / "04-kserve-inference" / "README.md"
        content = lab_readme.read_text()
        # Look for an actual command line installing v0.20.0 with --server-side.
        # Allow line continuations (\) between the flag and the URL.
        pattern = re.compile(
            r"kubectl\s+apply\s+--server-side[\s\S]{0,200}?"
            r"kserve/releases/download/v0\.20\.0/",
        )
        assert pattern.search(content), (
            "Lab 04 must include a `kubectl apply --server-side ... v0.20.0/...` "
            "command, not just reference v0.20.0 in explanatory text"
        )


class TestKnativeVersion:
    """Lab 04 must reference a current Knative Serving release, not the stale 1.17.0."""

    def test_no_stale_knative_117(self, repo_root: Path) -> None:
        """`knative-v1.17.0` must not appear in any final content file."""
        for md_file, content in _read_content_files(repo_root):
            rel = str(md_file.relative_to(repo_root))
            if "compass_artifact" in rel or "improvement-plan" in rel:
                continue
            for i, line in enumerate(content.split("\n"), 1):
                if "knative-v1.17.0" in line:
                    pytest.fail(
                        f"{rel}:{i} references stale knative-v1.17.0 (released Oct 2024). "
                        f"Update to a current 1.21+ release."
                    )

    def test_kserve_lab_uses_current_knative(self, repo_root: Path) -> None:
        """Every Knative reference in Lab 04 must be >= 1.21.

        Validate ALL matches, not just the first. A single stale reference
        anywhere in the file must fail the gate, regardless of ordering.
        """
        lab_readme = repo_root / "labs" / "04-kserve-inference" / "README.md"
        content = lab_readme.read_text()
        matches = re.findall(r"knative-v1\.(\d+)\.\d+", content)
        assert matches, "Lab 04 README missing a knative-v1.X.Y version reference"
        stale = [f"knative-v1.{m}" for m in matches if int(m) < 21]
        assert not stale, f"Lab 04 references Knative below the 1.21 floor: {sorted(set(stale))}"


class TestLlmdAttribution:
    """llm-d must be attributed as launched by Red Hat, not co-created equally."""

    def test_llmd_red_hat_attribution(self, repo_root: Path) -> None:
        """When llm-d is mentioned with contributors, Red Hat must be the launcher."""
        for md_file, content in _read_content_files(repo_root):
            rel = str(md_file.relative_to(repo_root))
            if "compass_artifact" in rel:
                continue
            lower = content.lower()
            if "llm-d" not in lower:
                continue
            # If the file mentions llm-d with multiple companies, Red Hat must be
            # distinguished as the launcher rather than listed as a peer.
            if ("co-created" in lower or "co-built" in lower) and "red hat" not in lower:
                pytest.fail(
                    f"{rel} describes llm-d as 'co-created/co-built' without "
                    f"distinguishing Red Hat as the project launcher"
                )


class TestGatewayRoutingLab:
    """Lab 05 must install every CRD its manifests need, pinned, before applying them.

    The lab once applied its Gateway, HTTPRoute, InferencePool and InferenceObjective
    manifests with no install step, so each apply failed with `no matches for kind`
    on a fresh cluster. The three groups come from three projects, each pinned to a
    release file. llm-d-router v1.0.0 still serves and stores InferenceObjective at
    llm-d.ai/v1alpha2, whose top-level spec fields are listed below. GAIE v1.6.2
    serves InferencePool only at inference.networking.k8s.io/v1; its spec and
    endpointPickerRef fields are listed below too.
    """

    LAB = Path("labs") / "05-gateway-routing"
    CRD_INSTALLS: ClassVar[dict[str, str]] = {
        "gateway.networking.k8s.io": (
            "https://github.com/kubernetes-sigs/gateway-api/releases/download/"
            "v1.6.3/standard-install.yaml"
        ),
        "inference.networking.k8s.io": (
            "https://github.com/kubernetes-sigs/gateway-api-inference-extension/releases/"
            "download/v1.6.2/v1-manifests.yaml"
        ),
        "llm-d.ai": "https://github.com/llm-d/llm-d-router/releases/download/v1.0.0/manifests.yaml",
    }
    OBJECTIVE_SPEC_FIELDS: ClassVar[set[str]] = {"poolRef", "poolRefs", "poolSelector", "priority"}
    POOL_SPEC_FIELDS: ClassVar[set[str]] = {
        "appProtocol",
        "endpointPickerRef",
        "selector",
        "targetPorts",
    }
    PICKER_REF_FIELDS: ClassVar[set[str]] = {"failureMode", "group", "kind", "name", "port"}

    def _readme(self, repo_root: Path) -> str:
        return (repo_root / self.LAB / "README.md").read_text()

    def _manifests(self, repo_root: Path) -> list[tuple[str, dict[str, Any]]]:
        docs: list[tuple[str, dict[str, Any]]] = []
        for path in sorted((repo_root / self.LAB / "manifests").glob("*.yaml")):
            rel = str(path.relative_to(repo_root))
            docs.extend((rel, doc) for doc in yaml.safe_load_all(path.read_text()) if doc)
        return docs

    def _command_lines(self, content: str, verb: str) -> list[tuple[int, str]]:
        return [
            (offset, line.strip())
            for offset, line in enumerate(content.splitlines())
            if line.strip().startswith(f"kubectl {verb} ")
        ]

    def test_every_manifest_group_has_a_crd_install(self, repo_root: Path) -> None:
        """Each non-core API group the manifests use maps to a pinned CRD install."""
        groups = {
            str(doc["apiVersion"]).split("/")[0]
            for _, doc in self._manifests(repo_root)
            if "/" in str(doc.get("apiVersion", ""))
        }
        assert groups, "Lab 05 has no manifests with a non-core apiVersion"
        missing = groups - set(self.CRD_INSTALLS)
        assert not missing, f"Lab 05 uses groups with no pinned CRD install: {sorted(missing)}"

    def test_readme_installs_crds_before_applying_manifests(self, repo_root: Path) -> None:
        """Every pinned CRD file is applied before the first `kubectl apply -f manifests/`."""
        applies = self._command_lines(self._readme(repo_root), "apply")
        first_manifest = next(
            (i for i, line in applies if "-f manifests/" in line),
            None,
        )
        assert first_manifest is not None, "Lab 05 never applies its manifests"
        for group, url in self.CRD_INSTALLS.items():
            at = [i for i, line in applies if line.endswith(f"-f {url}")]
            assert at, f"Lab 05 never applies the {group} CRDs from {url}"
            assert at[0] < first_manifest, (
                f"Lab 05 applies the {group} CRDs after its first manifest apply"
            )

    def test_gateway_api_install_is_server_side(self, repo_root: Path) -> None:
        """The Gateway API install guide applies standard-install.yaml with --server-side."""
        url = self.CRD_INSTALLS["gateway.networking.k8s.io"]
        lines = [ln for _, ln in self._command_lines(self._readme(repo_root), "apply") if url in ln]
        assert lines and all("--server-side" in ln for ln in lines), (
            f"Lab 05 must apply {url} with --server-side"
        )

    def test_cleanup_deletes_crds_in_reverse_order(self, repo_root: Path) -> None:
        """Clean up removes the CRD files after the lab's resources, last-installed first."""
        content = self._readme(repo_root)
        cleanup = content[content.index("## Clean up") :]
        deletes = [line for _, line in self._command_lines(cleanup, "delete")]
        crd_deletes = [
            (i, group)
            for i, line in enumerate(deletes)
            for group, url in self.CRD_INSTALLS.items()
            if line.endswith(f"-f {url}")
        ]
        order = [group for _, group in crd_deletes]
        expected = list(reversed(self.CRD_INSTALLS))
        assert order == expected, f"Clean up deletes CRDs as {order}, expected {expected}"
        last_resource = max(i for i, line in enumerate(deletes) if "-f manifests/" in line)
        assert last_resource < crd_deletes[0][0], "Clean up must delete resources before their CRDs"

    def test_objective_spec_fields_exist_in_crd_schema(self, repo_root: Path) -> None:
        """InferenceObjective uses only spec fields llm-d-router v1.0.0 serves at v1alpha2."""
        objectives = [
            (rel, doc)
            for rel, doc in self._manifests(repo_root)
            if doc.get("kind") == "InferenceObjective"
        ]
        assert objectives, "Lab 05 has no InferenceObjective manifest"
        for rel, doc in objectives:
            assert doc.get("apiVersion") == "llm-d.ai/v1alpha2", f"{rel}: {doc.get('apiVersion')}"
            unknown = set(doc.get("spec", {})) - self.OBJECTIVE_SPEC_FIELDS
            assert not unknown, f"{rel}: unknown InferenceObjective spec fields {sorted(unknown)}"

    def test_pool_spec_fields_exist_in_crd_schema(self, repo_root: Path) -> None:
        """InferencePool matches the v1 schema GAIE v1.6.2 serves, not the v1alpha2 one.

        The lab once used targetPortNumber, extensionRef, a bare selector map and an
        integer picker port under v1, which strict field validation rejects.
        """
        pools = [
            (rel, doc)
            for rel, doc in self._manifests(repo_root)
            if doc.get("kind") == "InferencePool"
        ]
        assert pools, "Lab 05 has no InferencePool manifest"
        for rel, doc in pools:
            assert doc.get("apiVersion") == "inference.networking.k8s.io/v1", rel
            spec = doc.get("spec", {})
            unknown = set(spec) - self.POOL_SPEC_FIELDS
            assert not unknown, f"{rel}: unknown InferencePool spec fields {sorted(unknown)}"

            selector = spec.get("selector")
            assert isinstance(selector, dict) and set(selector) <= {"matchLabels"}, (
                f"{rel}: v1 spec.selector holds only matchLabels, got {selector}"
            )
            assert isinstance(selector.get("matchLabels"), dict) and selector["matchLabels"], (
                f"{rel}: spec.selector.matchLabels is required and must not be empty"
            )

            ports = spec.get("targetPorts")
            assert isinstance(ports, list) and 1 <= len(ports) <= 8, (
                f"{rel}: spec.targetPorts must list 1 to 8 ports, got {ports}"
            )
            for port in ports:
                assert isinstance(port, dict) and set(port) == {"number"}, f"{rel}: {port}"
                assert isinstance(port["number"], int), f"{rel}: {port}"
            numbers = [port["number"] for port in ports]
            assert len(numbers) == len(set(numbers)), f"{rel}: duplicate targetPorts {numbers}"

            picker = spec.get("endpointPickerRef")
            if picker is None:
                continue
            unknown = set(picker) - self.PICKER_REF_FIELDS
            assert not unknown, f"{rel}: unknown endpointPickerRef fields {sorted(unknown)}"
            assert picker.get("name"), f"{rel}: endpointPickerRef.name is required"
            assert picker.get("failureMode", "FailClose") in {"FailOpen", "FailClose"}, rel
            if picker.get("kind", "Service") == "Service":
                port = picker.get("port")
                assert isinstance(port, dict) and isinstance(port.get("number"), int), (
                    f"{rel}: endpointPickerRef.port must be {{number: <int>}} for a Service"
                )

    def test_no_v1alpha2_pool_field_names(self, repo_root: Path) -> None:
        """Neither the README nor the manifests teach the retired v1alpha2 pool fields."""
        lab = repo_root / self.LAB
        for path in [lab / "README.md", *sorted((lab / "manifests").glob("*.yaml"))]:
            found = [
                name for name in ("targetPortNumber", "extensionRef") if name in path.read_text()
            ]
            assert not found, f"{path.relative_to(repo_root)} still names {found}"


class TestKagentLab:
    """Lab 06 must install and use the kagent CRDs as kagent v0.10.3 ships them.

    The lab once applied helm/crds/agent-crd.yaml from kagent's main branch, which
    kagent removed (HTTP 404), and its manifests used fields no kagent CRD ever
    served. kagent-crds 0.10.3 serves Agent and ModelConfig at kagent.dev/v1alpha2
    and bundles kmcp's MCPServer at kagent.dev/v1alpha1. The v1.0.0 alphas move to
    api.kagent.dev/v1alpha3 and have no MCPServer, so that group must not appear.
    The field lists below are the top-level spec properties of those CRD schemas.
    """

    LAB = Path("labs") / "06-kagent-mcp"
    CHART = "oci://ghcr.io/kagent-dev/kagent/helm/kagent-crds"
    CHART_VERSION = "0.10.3"
    API_VERSIONS: ClassVar[dict[str, str]] = {
        "Agent": "kagent.dev/v1alpha2",
        "ModelConfig": "kagent.dev/v1alpha2",
        "MCPServer": "kagent.dev/v1alpha1",
    }
    SPEC_FIELDS: ClassVar[dict[str, set[str]]] = {
        "Agent": {
            "allowedNamespaces",
            "byo",
            "declarative",
            "description",
            "documentationUrl",
            "iconUrl",
            "provider",
            "sandbox",
            "skills",
            "type",
            "version",
        },
        "ModelConfig": {
            "anthropic",
            "anthropicVertexAI",
            "apiKeyPassthrough",
            "apiKeySecret",
            "apiKeySecretKey",
            "azureOpenAI",
            "bedrock",
            "defaultHeaders",
            "foundry",
            "gemini",
            "geminiVertexAI",
            "model",
            "ollama",
            "openAI",
            "provider",
            "sapAICore",
            "tls",
        },
        "MCPServer": {"deployment", "httpTransport", "stdioTransport", "timeout", "transportType"},
    }

    def _manifests(self, repo_root: Path) -> list[tuple[str, dict[str, Any]]]:
        docs: list[tuple[str, dict[str, Any]]] = []
        for path in sorted((repo_root / self.LAB / "manifests").glob("*.yaml")):
            rel = str(path.relative_to(repo_root))
            docs.extend((rel, doc) for doc in yaml.safe_load_all(path.read_text()) if doc)
        return docs

    def _by_kind(self, repo_root: Path, kind: str) -> list[dict[str, Any]]:
        return [doc for _, doc in self._manifests(repo_root) if doc.get("kind") == kind]

    def test_readme_installs_pinned_crd_chart(self, repo_root: Path) -> None:
        """Step 1 installs the kagent-crds chart at the pinned version, not a branch URL."""
        content = (repo_root / self.LAB / "README.md").read_text()
        install = re.search(
            r"helm\s+install\s+kagent-crds\s+(\S+)\s+\\?\s*--version\s+(\S+)", content
        )
        assert install, "Lab 06 must install CRDs with `helm install kagent-crds ... --version`"
        assert install.groups() == (self.CHART, self.CHART_VERSION), (
            f"Lab 06 installs {install.groups()}, expected ({self.CHART}, {self.CHART_VERSION})"
        )
        assert "helm/crds/agent-crd.yaml" not in content, (
            "Lab 06 still references the removed helm/crds/agent-crd.yaml"
        )

    def test_no_kagent_v1_alpha_group(self, repo_root: Path) -> None:
        """api.kagent.dev belongs to the v1.0.0 alphas, which this lab does not pin."""
        bad = [
            f"{rel}: {doc.get('apiVersion')}"
            for rel, doc in self._manifests(repo_root)
            if str(doc.get("apiVersion", "")).startswith("api.kagent.dev/")
        ]
        assert not bad, "Lab 06 manifests use the kagent v1 alpha group:\n" + "\n".join(bad)

    def test_manifests_use_served_api_versions(self, repo_root: Path) -> None:
        """Each kagent kind declares the apiVersion kagent-crds 0.10.3 serves it at."""
        seen = set()
        bad: list[str] = []
        for rel, doc in self._manifests(repo_root):
            kind = doc.get("kind")
            if kind not in self.API_VERSIONS:
                continue
            seen.add(kind)
            if doc.get("apiVersion") != self.API_VERSIONS[kind]:
                bad.append(f"{rel}: {kind} at {doc.get('apiVersion')}")
        assert not bad, "Wrong apiVersion for kagent kinds:\n" + "\n".join(bad)
        assert seen == set(self.API_VERSIONS), f"Lab 06 is missing {set(self.API_VERSIONS) - seen}"

    def test_spec_fields_exist_in_crd_schema(self, repo_root: Path) -> None:
        """Every top-level spec field is one the CRD schema defines."""
        bad: list[str] = []
        for rel, doc in self._manifests(repo_root):
            allowed = self.SPEC_FIELDS.get(doc.get("kind", ""))
            if allowed is None:
                continue
            unknown = set(doc.get("spec", {})) - allowed
            if unknown:
                bad.append(f"{rel}: {doc['kind']} has unknown spec fields {sorted(unknown)}")
        assert not bad, "\n".join(bad)

    def test_agent_references_resolve(self, repo_root: Path) -> None:
        """The Agent's ModelConfig and MCP server references name resources in the lab."""
        model_configs = {doc["metadata"]["name"] for doc in self._by_kind(repo_root, "ModelConfig")}
        mcp_servers = {doc["metadata"]["name"] for doc in self._by_kind(repo_root, "MCPServer")}
        agents = self._by_kind(repo_root, "Agent")
        assert agents, "Lab 06 has no Agent manifest"
        for agent in agents:
            spec = agent["spec"]
            assert spec.get("type") == "Declarative" and "declarative" in spec, (
                "Lab 06's Agent must be type Declarative with a declarative block"
            )
            declarative = spec["declarative"]
            assert declarative.get("modelConfig") in model_configs, (
                f"Agent modelConfig {declarative.get('modelConfig')!r} not in {model_configs}"
            )
            for tool in declarative.get("tools", []):
                assert tool.get("type") == "McpServer", f"Unexpected tool type in {tool}"
                ref = tool["mcpServer"]
                assert (ref.get("apiGroup"), ref.get("kind")) == ("kagent.dev", "MCPServer"), (
                    f"Tool reference {ref} must be apiGroup kagent.dev, kind MCPServer"
                )
                assert ref.get("name") in mcp_servers, (
                    f"Tool reference {ref.get('name')!r} not in {mcp_servers}"
                )
