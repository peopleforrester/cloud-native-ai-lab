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
