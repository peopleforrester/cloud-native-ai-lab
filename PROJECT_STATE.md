# Project State: 2026-07 Version-Drift Refresh + PR #2 Review Cleanup

**Date:** 2026-07-12
**Branch:** staging (ahead of main; PR #2 open: staging → main)
**Plan:** [docs/improvement-plan.md](docs/improvement-plan.md)
**Verification method:** TDD — version-gating tests updated first (red), then
content edited to green. Every upstream version was re-verified against the
project's live GitHub releases on 2026-07-12 (not training data). Release-asset
URLs were confirmed reachable. **No live kind-cluster run was performed** — the
manifests parse and the install URLs resolve, but the lab flows have not been
executed end-to-end against a running cluster.

## 2026-07-12 refresh (on top of the June pass)

Re-verified all pins ~3 weeks after the June refresh. Drift found and applied:
- Kueue 0.18.1 → **0.18.3** (lab 01 Helm; OCI chart tag is `0.18.3`, no `v`).
- llm-d v0.7.0 → **v0.8.1** (docs; breaking-change note reworded to the v0.7 line).
- actions/checkout v6.0.3 → **v7.0.0** (major; the fork-PR-checkout hardening does
  not affect this push/pull_request workflow), setup-uv v8.2.0 → **v8.3.2**.
- Dev toolchain: mypy 2.1 → **2.2.0**, pytest 9.1 → **9.1.1**, ruff → **0.15.21**.
- All five project one-pager "Last verified" footers re-stamped to July 2026.

No drift (re-confirmed current 2026-07-12): JobSet v0.12.0, LeaderWorkerSet v0.9.0,
KServe v0.19.0, Knative Serving + net-kourier knative-v1.22.1, kagent tools 0.2.1,
kind v0.32.0, kindest/node v1.36.1, Kubernetes 1.36.x, MCP spec 2025-11-25,
Gateway API Inference Extension v1.5.0.

## Test status

71 tests passing across 8 test files. `ruff check`, `ruff format --check`, and
`mypy tests/` all green on Python 3.12.13 (pinned via `.python-version`).

## What this session did

Picked up after the April senior-review follow-up. Two drivers:
1. A full version-drift audit — everything pinned in April had drifted after
   ~7 weeks.
2. Clearing the 9 CodeRabbit review comments blocking PR #2.

| # | Phase | Commit |
|---|-------|--------|
| pre | pytest 9.0.2 → 9.0.3 (CVE-2025-71176) | `ef78682` |
| A | CI action pins (checkout v6.0.3, setup-uv v8.2.0); validate_ci exempts local actions; fact-check tests skip the gitignored claude-ai-context/ archive | `cbfaa62` |
| B | Dev toolchain: mypy 1.20→2.1, pytest 9.0.3→9.1, ruff→0.15.18, types-PyYAML latest | `0f44531` |
| C | Test hardening: validate_security asserts runAsUser + seccompProfile; Knative test checks all refs not just first; namespace check case/space-insensitive | `6d9f672` |
| D | Upstream version bumps (see below) + JobSet/KServe gating tests | `fe4b19b` |
| E | lab02 DRA kube-context step; improvement-plan Phase 3 block resolved; this file | (pending) |

## Version bumps applied (verified 2026-06-18)

| Project | April pin | Now |
|---------|-----------|-----|
| Kueue (lab 01 Helm) | 0.17.0 | 0.18.1 |
| JobSet (lab 03) | v0.11.1 | v0.12.0 |
| KServe (lab 04) | v0.17.0 | v0.19.0 |
| Knative Serving (lab 04) | knative-v1.21.2 | knative-v1.22.1 |
| net-kourier (lab 04) | knative-v1.21.0 | knative-v1.22.1 |
| LeaderWorkerSet (docs) | v0.8.0 | v0.9.0 |
| llm-d (docs) | v0.5 | v0.7.0 (+ breaking-change note) |
| kagent tools image (lab 06) | 0.1.4 | 0.2.1 |
| kind (lab 00) | v0.31.0 | v0.32.0 |
| kindest/node (lab 00) | v1.35.1 | v1.36.1 |
| README kind prereq floor | v0.27+ | v0.32+ |

No-drift / unchanged (confirmed current): MCP spec 2025-11-25; Gateway API
Inference `InferenceObjective`/`InferencePool` (ext v1.5.0); DRA GA-in-1.34
framing; kagent still CNCF Sandbox.

## Verified vs not verified

- **Verified:** all 71 tests pass; ruff/format/mypy green; every bumped version
  checked against its GitHub releases page; release-asset URLs reachable;
  kagent tools 0.2.1 is a real published tag.
- **NOT verified:** no lab was run on a live kind cluster this session. KServe
  0.17→0.19, Knative 1.21→1.22, Kueue 0.17→0.18, and JobSet 0.11→0.12 each cross
  a minor boundary and may carry CRD/API changes that only a cluster run would
  surface. llm-d v0.7.0 has documented breaking changes (NVIDIA 580+, standalone
  default mode) noted in its one-pager but not exercised.

## CodeRabbit (PR #2) status

All 9 comments addressed: the 3 Majors (Knative first-match test, security test
missing fields, DRA kube-context), the minors (CI SHA scope, namespace
brittleness, KServe time-relative wording, stale Phase 3 block), and the
"Critical" kagent-image flag (independently confirmed 0.1.4 was a real tag; now
bumped to 0.2.1 regardless).

## Next steps

- Push staging; confirm CI green and PR #2 turns mergeable with the review
  resolved.
- PR #1 (dependabot pytest 9.0.3) is now redundant — it auto-closes when staging
  merges, or can be closed manually.
- **Recurring maintenance reality:** exact version pins in long-lived teaching
  content drift roughly every 6–8 weeks. The scheduled 30-day check-in routine
  (`trig_01PwZGVCYdzFVDCUqNFWo9JL`) is the backstop; a periodic version sweep is
  the recurring cost of this pinning strategy.

## Out of scope (carried forward)

markdownlint / shellcheck CI, standardized per-lab cleanup sections, Helm chart
digest pinning, `.editorconfig`, PR/issue templates, nightly external-URL
validation job, `requires-python` floor revision. See improvement-plan.md.
