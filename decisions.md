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
