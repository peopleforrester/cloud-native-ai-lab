# ABOUTME: Offline check that the kind-cluster E2E plan in tests/e2e/lab_plan.py matches the labs.
# ABOUTME: Catches a pin bumped in a README but not in the plan, or a new install step it misses.

import shlex

import pytest

from tests.e2e.lab_plan import (
    INSTALL_SHAPED,
    KIND_CONFIG,
    LABS,
    LABS_DIR,
    NOT_RUN,
    Lab,
    manifest_commands,
    manifest_files,
    source_commands,
)

IDS = [lab.name for lab in LABS]


def test_plan_covers_every_lab() -> None:
    """A new lab directory must get a plan entry, or the E2E would silently never apply it."""
    lab_dirs = sorted(p.name for p in LABS_DIR.iterdir() if p.is_dir() and p.name[:2].isdigit())
    assert [lab.name for lab in LABS] == lab_dirs


def test_kind_config_exists() -> None:
    assert KIND_CONFIG.is_file()


@pytest.mark.parametrize("lab", LABS, ids=IDS)
def test_install_steps_are_the_labs_own(lab: Lab) -> None:
    """Every install command the E2E runs appears, as written, on the lab's main path."""
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
        f"{lab.name}/{lab.source} installs steps the E2E does not run: {unplanned}"
    )


@pytest.mark.parametrize("lab", LABS, ids=IDS)
def test_every_manifest_is_applied(lab: Lab) -> None:
    """The E2E puts every file in the lab's manifests/ through the API server."""
    commands = " ".join(manifest_commands(lab))
    for name in manifest_files(lab):
        assert f"manifests/{name}" in commands, f"{lab.name}: manifests/{name} is never applied"


@pytest.mark.parametrize("lab", LABS, ids=IDS)
def test_plan_commands_parse(lab: Lab) -> None:
    """The E2E runs each command without a shell, so each must split cleanly into argv."""
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
