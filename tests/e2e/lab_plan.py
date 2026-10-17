# ABOUTME: The install and apply plan the kind-cluster E2E runs, one entry per lab, in lab order.
# ABOUTME: Shared with tests/validate_e2e_plan.py, which keeps the plan in step with the lab READMEs.

import re
from dataclasses import dataclass
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent.parent
LABS_DIR = REPO_ROOT / "labs"
KIND_CONFIG = LABS_DIR / "00-setup" / "kind-cluster.yaml"
SETUP_SCRIPT = LABS_DIR / "00-setup" / "setup.sh"


@dataclass(frozen=True)
class Lab:
    """One lab: where its instructions live and the commands that install its controllers.

    `install` holds the lab's own commands, copied verbatim (continuations joined, whitespace
    collapsed) from `source`. The manifest applies are not listed here; `manifest_commands` reads
    them from the README so that a new apply step is picked up without touching this file.
    """

    name: str
    source: str
    install: tuple[str, ...]

    @property
    def path(self) -> Path:
        return LABS_DIR / self.name


LABS: tuple[Lab, ...] = (
    Lab(
        name="00-setup",
        source="setup.sh",
        install=(
            "helm repo add jetstack https://charts.jetstack.io --force-update",
            "helm repo update",
            (
                "helm upgrade --install cert-manager jetstack/cert-manager --namespace cert-manager "
                "--create-namespace --version v1.17.1 --set crds.enabled=true --wait --timeout 120s"
            ),
        ),
    ),
    Lab(
        name="01-kueue-basics",
        source="README.md",
        install=(
            (
                "helm install kueue oci://registry.k8s.io/kueue/charts/kueue --version 0.19.4 "
                "-n kueue-system --create-namespace --wait --timeout 5m"
            ),
            (
                "kubectl -n kueue-system wait --for=condition=Available "
                "deployment/kueue-controller-manager --timeout=120s"
            ),
        ),
    ),
    # Part B of lab 02 installs the DRA example driver into a separate demo cluster it builds
    # itself. Part A needs nothing beyond the resource.k8s.io/v1 API that Kubernetes serves by
    # default, so on the lab cluster the manifests apply with no driver installed.
    Lab(name="02-dra-resource-claims", source="README.md", install=()),
    Lab(
        name="03-jobset-training",
        source="README.md",
        install=(
            (
                "kubectl apply --server-side -f "
                "https://github.com/kubernetes-sigs/jobset/releases/download/v0.12.0/manifests.yaml"
            ),
            (
                "kubectl -n jobset-system wait --for=condition=Available "
                "deployment/jobset-controller-manager --timeout=120s"
            ),
        ),
    ),
    Lab(
        name="04-kserve-inference",
        source="README.md",
        install=(
            (
                "kubectl apply -f "
                "https://github.com/knative/serving/releases/download/knative-v1.23.0/serving-crds.yaml"
            ),
            (
                "kubectl apply -f "
                "https://github.com/knative/serving/releases/download/knative-v1.23.0/serving-core.yaml"
            ),
            (
                "kubectl apply -f https://github.com/knative-extensions/net-kourier/releases/download/"
                "knative-v1.23.0/kourier.yaml"
            ),
            (
                "kubectl patch configmap/config-network --namespace knative-serving --type merge "
                """--patch '{"data":{"ingress-class":"kourier.ingress.networking.knative.dev"}}'"""
            ),
            (
                "kubectl wait --for=condition=Available deployment --all -n knative-serving "
                "--timeout=120s"
            ),
            (
                "kubectl apply --server-side -f "
                "https://github.com/kserve/kserve/releases/download/v0.20.0/kserve.yaml"
            ),
            (
                "kubectl apply --server-side -f "
                "https://github.com/kserve/kserve/releases/download/v0.20.0/kserve-cluster-resources.yaml"
            ),
            (
                "kubectl wait --for=condition=Available deployment/kserve-controller-manager "
                "-n kserve --timeout=120s"
            ),
        ),
    ),
    # The lab README installs nothing: no Gateway API, Inference Extension or llm-d CRDs.
    Lab(name="05-gateway-routing", source="README.md", install=()),
    Lab(
        name="06-kagent-mcp",
        source="README.md",
        install=(
            (
                "kubectl apply -f "
                "https://raw.githubusercontent.com/kagent-dev/kagent/main/helm/crds/agent-crd.yaml"
            ),
        ),
    ),
)

# Install-shaped README commands the E2E deliberately does not run, each with the reason.
NOT_RUN = {
    (
        "02-dra-resource-claims",
        (
            "helm upgrade -i --create-namespace --namespace dra-example-driver "
            "dra-example-driver deployments/helm/dra-example-driver"
        ),
    ): "Part B installs into its own demo cluster from a local clone of the driver repo.",
}

# A command that installs something into the cluster from outside the lab's manifests/.
INSTALL_SHAPED = re.compile(
    r"^(?:helm\s+(?:install|upgrade|repo\s+add)\b|kubectl\s+apply\b.*https://)"
)
MANIFEST_APPLY = re.compile(r"^kubectl\s+(?:apply|create)\b.*\bmanifests/(\S+)")
SHELL_ASSIGNMENT = re.compile(r'^([A-Z_][A-Z0-9_]*)="([^"$]*)"$', re.MULTILINE)
QUIET_REDIRECT = re.compile(r"\s*>\s*/dev/null(?:\s+2>&1)?")


def _normalise(command: str) -> str:
    return " ".join(command.split())


@dataclass(frozen=True)
class Command:
    """A shell command as the lab shows it, with where it appears."""

    text: str
    line: int
    quoted: bool


def _join_continuations(lines: list[tuple[int, str, bool]]) -> list[Command]:
    commands: list[Command] = []
    parts: list[str] = []
    start, quoted = 0, False
    for lineno, line, in_quote in lines:
        if not parts:
            start, quoted = lineno, in_quote
        if line.rstrip().endswith("\\"):
            parts.append(line.rstrip()[:-1])
            continue
        parts.append(line)
        text = _normalise(" ".join(parts))
        if text and not text.startswith("#"):
            commands.append(Command(text, start, quoted))
        parts = []
    if parts:
        commands.append(Command(_normalise(" ".join(parts)), start, quoted))
    return commands


def readme_commands(lab: Lab) -> list[Command]:
    """Every command in the README's fenced code blocks, in order.

    A command inside a "> " blockquote is marked `quoted`: the labs use those for alternatives
    (an older KServe for an older kubectl) rather than for the main path.
    """
    lines: list[tuple[int, str, bool]] = []
    in_fence = False
    for lineno, raw in enumerate((lab.path / "README.md").read_text().splitlines(), start=1):
        quoted = bool(re.match(r"^\s*>", raw))
        line = re.sub(r"^\s*>\s?", "", raw)
        if line.lstrip().startswith("```"):
            in_fence = not in_fence
            continue
        if in_fence:
            lines.append((lineno, line, quoted))
    return _join_continuations(lines)


def script_commands(path: Path) -> list[Command]:
    """Every command in a shell script, with simple `NAME="value"` variables expanded.

    Output redirects to /dev/null are dropped: the E2E keeps output so a failure can be read.
    """
    text = path.read_text()
    variables = dict(SHELL_ASSIGNMENT.findall(text))
    lines: list[tuple[int, str, bool]] = []
    for lineno, raw in enumerate(text.splitlines(), start=1):
        line = raw
        for name, value in variables.items():
            line = line.replace(f'"${{{name}}}"', value).replace(f"${{{name}}}", value)
        lines.append((lineno, QUIET_REDIRECT.sub("", line), False))
    return _join_continuations(lines)


def source_commands(lab: Lab) -> list[Command]:
    if lab.source == "README.md":
        return readme_commands(lab)
    return script_commands(lab.path / lab.source)


def manifest_files(lab: Lab) -> list[str]:
    manifests = lab.path / "manifests"
    if not manifests.is_dir():
        return []
    return sorted(p.name for p in manifests.iterdir() if p.suffix in (".yaml", ".yml"))


def manifest_commands(lab: Lab) -> list[str]:
    """The commands that put every file in the lab's manifests/ onto the cluster.

    The README's own apply and create commands come first, in README order and with the flags it
    gives (`-n team-a-ns`, `create` for generateName Jobs). Any manifest the README never applies
    follows as a plain `kubectl apply -f`, so the whole directory reaches the API server.
    """
    commands: list[str] = []
    applied: set[str] = set()
    for command in readme_commands(lab):
        match = MANIFEST_APPLY.match(command.text)
        if match and not command.quoted:
            commands.append(command.text)
            applied.add(match.group(1))
    for name in manifest_files(lab):
        if name not in applied:
            commands.append(f"kubectl apply -f manifests/{name}")
    return commands
