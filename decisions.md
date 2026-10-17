# Decisions Log

Append-only audit trail of approvals, amendments, backward steps, and
conditional-skip rationales. See [[state-persistence]] for schema.

## 2026-08-30T12:38:19Z · init · state persistence initialized

`/init-state` ran in this repo. Lifecycle schema adopted per [[lifecycle-phases]]
(3 phases x 3 steps).

## 2026-08-30T12:38:19Z · migration · PROJECT_STATE.md migrated to the lifecycle schema

The prior PROJECT_STATE.md predated the lifecycle schema: no `Phase:` first
line, and its body still described a state that had not been true since July
(PR #2 open, staging ahead of main, 71 tests). The body was rewritten to current
fact and the lifecycle header prepended above it. Nothing was discarded; the
superseded July detail is preserved in git history.

Phase deduced as **3.3 Promote (complete)** from git state: clean tree, `main`
and `staging` identical at `9313345`, CI green on `main`, zero open issues, pull
requests, or Dependabot alerts.

**Approved line recorded as an unsealed approval rather than `pending`.** The
schema reserves `pending` for work still in 1.1 or 1.2. This work is shipped and
promoted, approved conversationally against `docs/improvement-plan.md` on
2026-04-26, but no sha256 was ever computed over the plan body. Sealing one now
would fabricate a contract that did not exist at the time, so the gap is
recorded rather than backfilled.

## 2026-08-30T12:38:19Z · 3.3 · Conditional-step and scope notes carried into state

- **No live kind-cluster validation**, across every version refresh in this
  repo. Manifests parse and install URLs resolve; behaviour on a running cluster
  is unverified. Recorded so a later session does not read green CI as
  end-to-end proof.
- **`docs/projects/aaif.md` deliberately left at March 2026.** It was not
  re-verified during the July sweep, so it was not stamped.
- **`docs/talk-outline.md` is frozen by design.** It records a talk delivered on
  24 March 2026. Version sweeps must skip it. Twice now a sweep has updated it
  and falsified what was said on stage.

## 2026-09-17T01:19:38Z · 3.3 · September 2026 currency sweep

Nine weeks since the last full verification. Every pin re-checked against the
project's own releases. Kueue, KServe, Knative, net-kourier, LeaderWorkerSet and
kind all moved; JobSet, the kagent tools image and actions/checkout had not.
Kubernetes 1.37.0 is now stable and the MCP spec advanced to the 2026-07-28
revision, which removes the initialize handshake in favour of a stateless core
and deprecates Sampling, Roots and Logging.

### CORRECTED: lab 05 taught an InferenceObjective CRD that never existed

**What was wrong:** `labs/05-gateway-routing/manifests/inference-objective.yaml`
declared `kind: InferenceObjective` under `apiVersion:
inference.networking.k8s.io/v1`, and its spec used `modelName`, `criticality`
and `targetModels`.

**Why:** two independent errors that had been there since the file was written,
not drift introduced by a later release.

1. That apiVersion has never served that kind. Reading the CRD files tag by tag
   across GAIE v0.3.0 through v1.6.1 shows `InferenceObjective` replaced
   `InferenceModel` in v1.0.0 but stayed at
   `inference.networking.x-k8s.io/v1alpha2`. Only `InferencePool` was promoted
   to the GA group in that release. v1.6.0 removed the objective entirely and
   llm-d-router now serves it at `llm-d.ai/v1alpha2`.
2. The three spec fields belong to the `InferenceModel` that was replaced in
   v1.0.0. `InferenceObjective` has only ever had `poolRef` and an integer
   `priority`.

**Do not suggest:** writing `InferenceObjective` under
`inference.networking.k8s.io/v1`, under `inference.networking.x-k8s.io/v1alpha2`
(GAIE's own wording for what it removed, but not a group llm-d serves), or
restoring `modelName`/`criticality`/`targetModels`. `criticality` did not become
a rename of `priority`: the type changed from a string enum to int32 with no
fixed translation.

**Status:** Permanent for the GA-group claim. Revisit the llm-d group only if
llm-d-router re-homes the CRD again.

**Gate added:** `TestInferenceObjective::test_inference_objective_uses_llm_d_group`
fails on any manifest declaring the kind without `llm-d.ai/v1alpha2`. Verified by
reverting the apiVersion and watching it fail, rather than assuming.

### Note: ruff 0.16 widened what CI checks

0.16 formats Markdown as well as Python, so `ruff format --check .` now covers 42
files here rather than 11, and its default rule set grew (0.15 passed this tree
clean, 0.16 flagged SIM102). Both were confirmed by running the two versions
side by side. Everything passes, so this was adopted rather than pinned back.

## 2026-10-17T08:55:59Z · 3.3 · conference-knowledge owns conference information (#8)

`peopleforrester/conference-knowledge` became the source of truth for event
state on 2026-10-03. Swept the tree for conference material. Found no CFP notes,
submission status, attendance plans, organizer contacts or travel. Found three
places that state facts about KubeCon EU 2026:

- `docs/talk-outline.md` header: Cloud Native University, Tuesday 24 March 2026,
  13:20, RAI Amsterdam Convention Center.
- `README.md` attribution: delivered 24 March 2026 at the RAI in Amsterdam.
- `docs/landscape-report.md`: the event ran 23-26 March 2026 at the RAI with
  12,000+ expected attendees, as written in March 2026.

**Kept, not replaced with pointers.** These are the published record of a talk
already given and a dated report, not live event state. The outline is frozen by
design (see the 2026-08-30 entry), and swapping public prose for a pointer to a
private repo would leave readers of a public resource with a dead reference. The
speaking-record facts were handed to conference-knowledge as an `agent-task`
follow-up so its record can be checked against this source, and AGENTS.md now
has a "Where things live" section pointing there.

**Do not suggest:** adding CFP dates, future events, attendance plans or travel
to this repo. They belong in conference-knowledge.

## 2026-10-17T12:17:18Z · 3.3 · Kind-cluster E2E added, not yet run on a cluster (#13)

`tests/e2e/validate_kind_cluster.py` creates a kind cluster from
`labs/00-setup/kind-cluster.yaml`, checks the three nodes and their zone labels,
then works through labs 00 to 06 in order on that one cluster. For each lab it
runs the lab's install steps and applies every file in its `manifests/`. Labs
share the cluster because lab 03 queues a JobSet through lab 01's Kueue queue.

**The plan follows the labs; it does not restate them.** The install commands
in `tests/e2e/lab_plan.py` are the README's (or `setup.sh`'s) own commands,
verbatim. `tests/validate_e2e_plan.py` runs offline in the Test command and
fails in either direction: a plan command the lab no longer shows (a bumped
pin), or an install-shaped command the lab shows but the plan does not run. Each
was checked by editing a README and watching the test fail. Manifest applies are
read from the README in order, keeping its `-n` flags and `create` for
generateName Jobs. Any manifest the README never applies is applied afterwards,
so every file reaches the API server. Lab 02's `resource-claim-template.yaml` is
the only such file today.

**Isolated from the learner's own setup.** The cluster is named `cnai-lab-e2e`,
not `ai-workshop`, so the suite never reuses or deletes a learner's cluster. It
fails rather than adopting a `cnai-lab-e2e` that already exists. kubectl and
Helm get their own kubeconfig and Helm home in the pytest temp dir. Commands
run without a shell, and output is captured so a failure shows stdout and
stderr.

**Not yet run against a live cluster.** On the run host kind, kubectl and helm
are not installed, and the Docker daemon refuses this user. The suite was
exercised with stub binaries that log each call, which confirmed the command
sequence, working directories, the isolated environment and teardown. Against
the real host it errors on every test with `Missing: kind, kubectl, helm`. With
the tools stubbed it errors with the `docker info` permission failure. Both exit
non-zero. The 2026-08-30 note still holds: no lab has been validated on a live
cluster.

**Expected red on first live run, left visible rather than excluded:**

- Lab 05 has no install step, so `gateway.yaml`, `inference-pool.yaml` and
  `inference-objective.yaml` will be rejected because their kinds are not
  served. The lab needs Gateway API, Inference Extension and llm-d-router CRD
  installs, which is a lab content change.
- Lab 06's kagent CRD URL returns 404 (found by #10). The E2E stops lab 06 at
  that install step.

Lab 02 Part B builds its own demo cluster for the DRA example driver, so its
`helm upgrade -i` is listed in `NOT_RUN` with that reason. Part A's manifests
use the built-in `resource.k8s.io/v1` API and apply on the lab cluster with no
driver. The pod stays Pending, which is expected without a driver.

No new dependency: the suite uses the standard library and pytest only.
