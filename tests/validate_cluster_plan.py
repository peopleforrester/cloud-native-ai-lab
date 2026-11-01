# ABOUTME: Offline check that the kind-cluster plan in tests/cluster/lab_plan.py matches the labs.
# ABOUTME: Catches a pin bumped in a README but not in the plan, or a new install step it misses.

import re
import shlex

import pytest

from tests.cluster.kind_cluster import (
    HELM_SHA256,
    HELM_VERSION,
    helm_platform,
    helm_url,
    webhook_not_yet_serving,
)
from tests.cluster.lab_plan import (
    INSTALL_SHAPED,
    KIND_CONFIG,
    LABS,
    LABS_DIR,
    MANIFEST_APPLY,
    NOT_RUN,
    Lab,
    manifest_commands,
    manifest_files,
    readme_commands,
    source_commands,
    uses_generate_name,
)

IDS = [lab.name for lab in LABS]


def test_plan_covers_every_lab() -> None:
    """A new lab directory must get a plan entry, or the cluster check would never apply it."""
    lab_dirs = sorted(p.name for p in LABS_DIR.iterdir() if p.is_dir() and p.name[:2].isdigit())
    assert [lab.name for lab in LABS] == lab_dirs


def test_kind_config_exists() -> None:
    assert KIND_CONFIG.is_file()


@pytest.mark.parametrize("lab", LABS, ids=IDS)
def test_install_steps_are_the_labs_own(lab: Lab) -> None:
    """Every install command the cluster check runs appears, as written, on the lab's main path."""
    shown = {c.text for c in source_commands(lab) if not c.quoted}
    missing = [command for command in lab.install if command not in shown]
    assert not missing, f"{lab.name}/{lab.source} no longer shows: {missing}"


@pytest.mark.parametrize("lab", LABS, ids=IDS)
def test_plan_runs_every_install_step(lab: Lab) -> None:
    """Every install-shaped command on the lab's main path is in the plan, or excused in NOT_RUN."""
    unplanned = [
        f"line {c.line}: {c.text}"
        for c in source_commands(lab)
        if not c.quoted
        and INSTALL_SHAPED.match(c.text)
        and c.text not in lab.install
        and (lab.name, c.text) not in NOT_RUN
    ]
    assert not unplanned, (
        f"{lab.name}/{lab.source} installs steps the cluster check does not run: {unplanned}"
    )


@pytest.mark.parametrize("lab", LABS, ids=IDS)
def test_every_manifest_is_applied(lab: Lab) -> None:
    """The cluster check puts every file in the lab's manifests/ through the API server."""
    commands = " ".join(manifest_commands(lab))
    for name in manifest_files(lab):
        assert f"manifests/{name}" in commands, f"{lab.name}: manifests/{name} is never applied"


@pytest.mark.parametrize("lab", LABS, ids=IDS)
def test_plan_commands_parse(lab: Lab) -> None:
    """The cluster check runs each command without a shell, so each must split cleanly into argv."""
    for command in (*lab.install, *manifest_commands(lab)):
        argv = shlex.split(command)
        assert argv[0] in ("kubectl", "helm"), command


def test_manifest_commands_follow_the_readme() -> None:
    """README applies keep their order and flags; manifests the README never applies come last."""
    kueue = manifest_commands(LABS[1])
    assert kueue[0] == "kubectl apply -f manifests/resource-flavor.yaml"
    assert "kubectl create -f manifests/sample-job-b.yaml -n team-b-ns" in kueue
    assert len(kueue) == len(manifest_files(LABS[1]))
    dra = manifest_commands(LABS[2])
    assert dra[-1] == "kubectl apply -f manifests/resource-claim-template.yaml"


@pytest.mark.parametrize("lab", LABS, ids=IDS)
def test_generate_name_manifests_are_created(lab: Lab) -> None:
    """A README must submit a generateName manifest with `kubectl create`: `apply` refuses it.

    The kind-cluster check found lab 01 telling learners to `kubectl apply` sample-job.yaml.
    """
    wrong = [
        f"line {c.line}: {c.text}"
        for c in readme_commands(lab)
        if (match := MANIFEST_APPLY.match(c.text))
        and c.text.split()[1] == "apply"
        and uses_generate_name(lab.path / "manifests" / match.group(1))
    ]
    assert not wrong, f"{lab.name}/README.md applies generateName manifests: {wrong}"


def test_cluster_check_pins_a_helm_3_release() -> None:
    """The labs ask for Helm 3.x, so the check runs them with a Helm 3 release, never a 4.x one.

    Helm 4.2.1, the gate's own `helm`, hangs in lab 00's cert-manager install.
    """
    assert re.fullmatch(r"v3\.\d+\.\d+", HELM_VERSION), HELM_VERSION
    readme = (LABS_DIR.parent / "README.md").read_text()
    assert "Helm](https://helm.sh/docs/intro/install/) 3.x" in readme


@pytest.mark.parametrize(
    ("system", "machine", "expected"),
    [
        ("Linux", "x86_64", "linux-amd64"),
        ("Linux", "aarch64", "linux-arm64"),
        ("Darwin", "arm64", "darwin-arm64"),
        ("Darwin", "x86_64", "darwin-amd64"),
    ],
)
def test_helm_platform_names_a_pinned_download(system: str, machine: str, expected: str) -> None:
    assert helm_platform(system, machine) == expected
    assert expected in HELM_SHA256
    assert helm_url(expected) == f"https://get.helm.sh/helm-{HELM_VERSION}-{expected}.tar.gz"


def test_a_host_without_a_pinned_helm_is_not_matched() -> None:
    """A platform with no pinned sum fails the check up front instead of running unverified."""
    assert helm_platform("Linux", "riscv64") not in HELM_SHA256
    assert helm_platform("Windows", "AMD64") not in HELM_SHA256


def test_helm_sums_are_sha256() -> None:
    assert all(re.fullmatch(r"[0-9a-f]{64}", digest) for digest in HELM_SHA256.values())


def test_only_a_refused_webhook_call_is_waited_out() -> None:
    """The cluster check reruns a manifest only while a webhook refuses connections."""
    refused = (
        'Error from server (InternalError): error when creating "manifests/jobset-simple.yaml": '
        'Internal error occurred: failed calling webhook "mjobset.kb.io": failed to call webhook: '
        'Post "https://jobset-webhook-service.jobset-system.svc:443/mutate": dial tcp '
        "10.96.135.168:443: connect: connection refused"
    )
    assert webhook_not_yet_serving(refused)
    assert not webhook_not_yet_serving(
        "error: from sample-job-: cannot use generate name with apply"
    )
    assert not webhook_not_yet_serving(
        'Error from server (Forbidden): admission webhook "vjobset.kb.io" denied the request'
    )
    assert not webhook_not_yet_serving('no matches for kind "ClusterStorageContainer"')
