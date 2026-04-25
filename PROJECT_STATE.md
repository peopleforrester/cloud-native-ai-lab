# Project State: 2026-04 Senior Review Follow-up

**Date:** 2026-04-26
**Branch:** staging (clean, ahead of main)
**Plan:** [docs/improvement-plan.md](docs/improvement-plan.md)
**Verification method:** TDD — every phase wrote a failing test first, fixed
the code, ran the full test suite, then committed. URLs were verified with
`curl -I` against GitHub releases. No live cluster verification was performed
(no kind cluster available); manifests are syntactically valid and behavioral
assertions remain unverified against a running cluster.

## Test status

71 tests passing across 8 test files (was 55 before this work; +16 new).

## Phases completed

| # | Title                                        | Commit      |
|---|----------------------------------------------|-------------|
| 1 | Tooling baseline — ruff/format/mypy clean    | `4221e8e`   |
| 2 | CI workflow hardening — perms/concurrency/SHAs | `069b23d` |
| 3 | mcp-server image — wrong path AND :latest    | `b1eaf2d`   |
| 4 | Knative pins to current stable (1.21)        | `2de63cb`   |
| 5 | KServe v0.17.0 with --server-side recommended | `84a1ce2`  |
| 6 | Lab 02 DRA driver path correction            | `f5092f8`   |
| 7 | Declarative namespace creation across labs   | `f0b204a`   |
| 8 | securityContext teaching pattern (lab 01)    | `5150846`   |

## Verification status

- **Tests:** all 71 pass locally on Python 3.12.13.
- **Lint/format/types:** `uv run ruff check .`, `uv run ruff format --check .`,
  `uv run mypy tests/` — all green. CLAUDE.md commands honor their promise.
- **CI workflow:** parses cleanly, has `permissions: contents: read`,
  concurrency cancellation, 10-minute timeout, lint gates, SHA-pinned
  third-party actions.
- **Upstream URLs verified with `curl -I`:**
  - `knative-v1.21.2/serving-crds.yaml` → 200
  - `knative-v1.21.2/serving-core.yaml` → 200
  - `knative-extensions/net-kourier/.../knative-v1.21.0/kourier.yaml` → 200
  - `kserve/v0.17.0/kserve.yaml` → 200
  - `kserve/v0.17.0/kserve-cluster-resources.yaml` → 200
- **Image reference verified:** `ghcr.io/kagent-dev/kagent/tools:0.1.4` is a
  real published artifact (kagent-dev/tools v0.1.4, 2026-04-01).
- **NOT verified against a live cluster:** the lab 01 securityContext changes
  and the lab 02 DRA driver demo flow have not been executed end-to-end.
  Local kind verification deferred.

## Next steps

Open the staging→main PR once Michael has reviewed. Items deferred (not in
scope for this round):

- markdownlint / shellcheck CI integration
- Standardized cleanup sections per lab
- Helm chart digest pinning
- `.editorconfig`, PR/issue templates
- One-pager Knative version pin
- Tighter `_strip_code_blocks` regex in `validate_markdown.py`
- Nightly external-URL validation job
- `requires-python` floor revision

These are documented in `docs/improvement-plan.md` under "Out of scope."

## Open question parked

Phase 3 picked **option 1** (`ghcr.io/kagent-dev/kagent/tools:0.1.4`) for the
mcp-server image without explicit confirmation. Alternatives were:

- (2) `ghcr.io/containers/kubernetes-mcp-server:<tag>` — focused, unaffiliated.
- (3) Leave as illustrative with a warning comment.

Override possible by editing `labs/06-kagent-mcp/manifests/mcp-server.yaml`.
