# ABOUTME: Runs the labs on a real kind cluster: create it, install, apply manifests. In the E2E command.
# ABOUTME: Fetches its own pinned Helm 3; fails loudly without kind, kubectl, Docker or outbound HTTPS.

import hashlib
import io
import os
import platform
import shlex
import shutil
import subprocess
import tarfile
import time
import urllib.error
import urllib.request
from collections.abc import Iterator
from pathlib import Path

import pytest

from tests.cluster.lab_plan import KIND_CONFIG, LABS, Lab, manifest_commands

# Its own name, not the lab's `ai-workshop`, so the suite never reuses or deletes a learner's
# cluster on the same host. The node image, port mappings and labels still come from the lab file,
# so a running `ai-workshop` cluster holds host ports 30000-30002 and `kind create` fails on them.
CLUSTER_NAME = "cnai-lab-check"
REQUIRED_TOOLS = ("docker", "kind", "kubectl")
COMMAND_TIMEOUT_SECONDS = 900
WEBHOOK_SETTLE_SECONDS = 60
# The check runs the labs with this Helm, downloaded and checked against its sha256, not with
# whatever `helm` the host has. The labs ask for Helm 3.x (README prerequisites, `get-helm-3` in
# lab 00), and the gate's own Helm is 4.2.1, which never returns from lab 00's `helm upgrade
# --install cert-manager ... --wait`: after the pods are Ready it waits on deleting the
# startupapicheck hook Job, which does not exist yet, until the command is killed. Helm 3.22.1
# finishes the same install in about 90 seconds. The sums are get.helm.sh's, fetched 2026-11-01.
HELM_VERSION = "v3.22.1"
HELM_SHA256 = {
    "linux-amd64": "896cf63684a42a723d61c980369d6e588330927deb13676ca0d85006dd6da0ea",
    "linux-arm64": "4c29e286b279d170fa048ddfc3e4e83dcd069ca9c52102766ba672d7149e694d",
    "darwin-amd64": "cf850a81b908f8eef0331e6b18776da2767bcac639ca84472311dad20008495c",
    "darwin-arm64": "e73da8a0b0d5193774fdff17ce6319c7436bb22ee229b45fd64f3c40368c753a",
}
HELM_ARCH = {"x86_64": "amd64", "amd64": "amd64", "aarch64": "arm64", "arm64": "arm64"}
DOWNLOAD_TIMEOUT_SECONDS = 120


def helm_platform(system: str, machine: str) -> str:
    """The get.helm.sh platform name for platform.system() and platform.machine()."""
    return f"{system.lower()}-{HELM_ARCH.get(machine.lower(), machine.lower())}"


def helm_url(target: str) -> str:
    """Where get.helm.sh serves HELM_VERSION for a helm_platform() name."""
    return f"https://get.helm.sh/helm-{HELM_VERSION}-{target}.tar.gz"


def _run(argv: list[str], env: dict[str, str], cwd: Path) -> subprocess.CompletedProcess[str]:
    try:
        return subprocess.run(
            argv,
            env=env,
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=COMMAND_TIMEOUT_SECONDS,
            check=False,
        )
    except subprocess.TimeoutExpired as err:
        return subprocess.CompletedProcess(
            argv,
            returncode=-1,
            stdout=_text(err.stdout),
            stderr=f"{_text(err.stderr)}\nkilled after {COMMAND_TIMEOUT_SECONDS}s".strip(),
        )


def webhook_not_yet_serving(stderr: str) -> bool:
    """True when the API server could not reach an admission webhook, so nothing was created."""
    return "failed calling webhook" in stderr and "connect: connection refused" in stderr


def _run_after_webhook_settles(
    command: str, env: dict[str, str], cwd: Path
) -> subprocess.CompletedProcess[str]:
    """Run a manifest command, waiting out a webhook that is not yet answering.

    Kueue's and JobSet's webhooks can refuse connections for about a second after the lab's own
    `kubectl wait --for=condition=Available` returns: on four fresh JobSet installs, the first
    apply was refused twice and went through 1.2 seconds later. A learner typing the next command
    never sees that gap, and a refused call creates nothing, so the command runs again for up to
    WEBHOOK_SETTLE_SECONDS. Any other error, or a webhook still refusing after that, fails.
    Install steps never get this wait, so a lab that applies before its controller runs still fails.
    """
    deadline = time.monotonic() + WEBHOOK_SETTLE_SECONDS
    while True:
        result = _run(shlex.split(command), env, cwd)
        if not webhook_not_yet_serving(result.stderr) or time.monotonic() > deadline:
            return result
        time.sleep(2)


def _text(output: bytes | str | None) -> str:
    if isinstance(output, bytes):
        return output.decode(errors="replace")
    return output or ""


def _describe(command: str, result: subprocess.CompletedProcess[str]) -> str:
    return (
        f"$ {command}\nexit {result.returncode}\n"
        f"--- stdout\n{result.stdout.strip()}\n--- stderr\n{result.stderr.strip()}"
    )


@pytest.fixture(scope="session")
def tools() -> None:
    """Fail every test up front, naming what is missing, when this host cannot run kind."""
    missing = [tool for tool in REQUIRED_TOOLS if shutil.which(tool) is None]
    if missing:
        pytest.fail(
            "The kind-cluster check needs kind, kubectl and docker on PATH. "
            f"Missing: {', '.join(missing)}",
            pytrace=False,
        )
    info = subprocess.run(["docker", "info"], capture_output=True, text=True, check=False)
    if info.returncode != 0:
        pytest.fail(
            "The kind-cluster check needs a Docker daemon this user can reach, and "
            f"`docker info` failed:\n{info.stderr.strip()}",
            pytrace=False,
        )


@pytest.fixture(scope="session")
def helm_dir(tmp_path_factory: pytest.TempPathFactory) -> Path:
    """Download HELM_VERSION for this host, check its sha256, and return the directory holding it."""
    target = helm_platform(platform.system(), platform.machine())
    if target not in HELM_SHA256:
        pytest.fail(
            f"The kind-cluster check pins Helm {HELM_VERSION} for {', '.join(HELM_SHA256)}, "
            f"and this host is {target}.",
            pytrace=False,
        )
    url = helm_url(target)
    try:
        with urllib.request.urlopen(url, timeout=DOWNLOAD_TIMEOUT_SECONDS) as response:
            archive = response.read()
    except (urllib.error.URLError, TimeoutError, OSError) as err:
        pytest.fail(
            f"The kind-cluster check needs outbound HTTPS to fetch Helm from {url}: {err}",
            pytrace=False,
        )
    digest = hashlib.sha256(archive).hexdigest()
    if digest != HELM_SHA256[target]:
        pytest.fail(
            f"{url} has sha256 {digest}, and the check pins {HELM_SHA256[target]}.", pytrace=False
        )
    bin_dir = tmp_path_factory.mktemp("helm")
    helm = bin_dir / "helm"
    with tarfile.open(fileobj=io.BytesIO(archive), mode="r:gz") as tar:
        member = tar.extractfile(f"{target}/helm")
        assert member is not None, f"{url} has no {target}/helm"
        helm.write_bytes(member.read())
    helm.chmod(0o755)
    version = subprocess.run(
        [str(helm), "version", "--template", "{{.Version}}"],
        capture_output=True,
        text=True,
        check=False,
    )
    assert version.stdout.strip() == HELM_VERSION, _describe(f"{helm} version", version)
    return bin_dir


@pytest.fixture(scope="session")
def cluster_env(
    tools: None, helm_dir: Path, tmp_path_factory: pytest.TempPathFactory
) -> Iterator[dict[str, str]]:
    """Create the lab cluster from labs/00-setup/kind-cluster.yaml and delete it afterwards.

    The pinned Helm comes first on PATH, so every lab's `helm` command runs it. kubectl and helm
    get a kubeconfig and Helm home of their own under the pytest temp dir, so the run neither
    switches the user's current context nor adds repos to their Helm config.
    """
    home = tmp_path_factory.mktemp("kind-check")
    kubeconfig = home / "kubeconfig"
    env = {
        **os.environ,
        "PATH": f"{helm_dir}{os.pathsep}{os.environ.get('PATH', '')}",
        "KUBECONFIG": str(kubeconfig),
        "HELM_CACHE_HOME": str(home / "helm-cache"),
        "HELM_CONFIG_HOME": str(home / "helm-config"),
        "HELM_DATA_HOME": str(home / "helm-data"),
    }
    existing = _run(["kind", "get", "clusters"], env, home)
    if CLUSTER_NAME in existing.stdout.split():
        pytest.fail(
            f"A kind cluster named {CLUSTER_NAME} already exists, probably from an interrupted run. "
            f"Delete it with `kind delete cluster --name {CLUSTER_NAME}` and run again.",
            pytrace=False,
        )
    argv = ["kind", "create", "cluster", "--config", str(KIND_CONFIG), "--name", CLUSTER_NAME]
    argv += ["--kubeconfig", str(kubeconfig), "--wait", "300s"]
    create = shlex.join(argv)
    result = _run(argv, env, home)
    if result.returncode != 0:
        _run(["kind", "delete", "cluster", "--name", CLUSTER_NAME], env, home)
        pytest.fail(
            f"Could not create the lab cluster.\n{_describe(create, result)}", pytrace=False
        )
    try:
        yield env
    finally:
        _run(["kind", "delete", "cluster", "--name", CLUSTER_NAME], env, home)


def test_cluster_matches_lab_00(cluster_env: dict[str, str]) -> None:
    """Lab 00 promises three Ready nodes: one control plane and two labelled simulated-GPU workers."""
    zones = [
        "kubectl",
        "get",
        "nodes",
        "-l",
        "node.kubernetes.io/gpu-type=simulated",
        "-o",
        r"jsonpath={.items[*].metadata.labels.topology\.kubernetes\.io/zone}",
    ]
    command = shlex.join(zones)
    result = _run(zones, cluster_env, KIND_CONFIG.parent)
    assert result.returncode == 0, _describe(command, result)
    assert sorted(result.stdout.split()) == ["zone-a", "zone-b"], _describe(command, result)
    wait = "kubectl wait --for=condition=Ready nodes --all --timeout=300s"
    ready = _run(shlex.split(wait), cluster_env, KIND_CONFIG.parent)
    assert ready.returncode == 0, _describe(wait, ready)
    assert ready.stdout.count("condition met") == 3, _describe(wait, ready)


# Labs run in order on one cluster, as a learner works through them: lab 03 queues a JobSet
# through the Kueue LocalQueue that lab 01 created.
@pytest.mark.parametrize("lab", LABS, ids=[lab.name for lab in LABS])
def test_lab_installs_and_applies(cluster_env: dict[str, str], lab: Lab) -> None:
    """Install the lab's controllers at their pinned versions, then apply all of its manifests/.

    An install failure stops the lab, since nothing after it can apply. Apply failures are
    collected so one run reports every manifest the API server rejects.
    """
    for command in lab.install:
        result = _run(shlex.split(command), cluster_env, lab.path)
        assert result.returncode == 0, (
            f"Lab {lab.name}: install step failed.\n{_describe(command, result)}"
        )
    failures: list[str] = []
    for command in manifest_commands(lab):
        result = _run_after_webhook_settles(command, cluster_env, lab.path)
        if result.returncode != 0:
            failures.append(_describe(command, result))
    assert not failures, f"Lab {lab.name}: manifests rejected.\n\n" + "\n\n".join(failures)
