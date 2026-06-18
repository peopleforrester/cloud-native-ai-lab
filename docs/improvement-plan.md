<!-- ABOUTME: Phased improvement plan derived from the 2026-04-25 senior review. -->
<!-- ABOUTME: Each phase is TDD: failing test first, then implementation, then commit. -->

# Improvement Plan: 2026-04 Senior Review Follow-up

Source: `/review-senior` pass on 2026-04-25. Critical issues: 0. This plan addresses
the High and Medium priority items in priority order. Each phase follows TDD:
write a failing test, implement to green, commit to `staging`.

## Working rules

- Branch: `staging` (per global git workflow rule). Push to `staging` only.
- One phase per commit. Each commit references the phase number.
- Tests added in `tests/` follow the existing `validate_*.py` naming.
- No timeline estimates. Phases are sequenced; cadence is "as soon as the prior
  phase is green."

## Verified upstream facts (2026-04-26)

These were verified before drafting the plan and are the source of truth for
versions and image references in the changes below:

- **Knative Serving**: latest stable is `v1.21.2` (released 2026-03-24).
  Source: github.com/knative/serving/releases.
- **DRA example driver**: lives at `kubernetes-sigs/dra-example-driver`, latest
  release `v0.2.1` (2026-01-09). Helm-only install — no `kubectl apply -f`
  path exists upstream.
- **kagent kubernetes MCP image**: `ghcr.io/kagent-dev/kubernetes-mcp-server`
  does not exist. The kubernetes MCP tools ship inside the consolidated
  `ghcr.io/kagent-dev/kagent/tools` image (latest `0.1.4`, 2026-04-01). An
  unaffiliated alternative is `ghcr.io/containers/kubernetes-mcp-server`.

## Phase 3 image decision (resolved)

The original `labs/06-kagent-mcp/manifests/mcp-server.yaml` referenced an image
path that did not exist (`ghcr.io/kagent-dev/kubernetes-mcp-server:latest`).
**Resolved with option 1:** the manifest now points at the officially-shipped
`ghcr.io/kagent-dev/kagent/tools` image (pinned to a real tag), with the
manifest `tools:` list filtering it down to the Kubernetes subset — the most
idiomatic choice for the kagent ecosystem. The unaffiliated
`ghcr.io/containers/kubernetes-mcp-server` and a purely-illustrative manifest
were the considered alternatives. The pinned tag is kept current as part of the
repo's version-drift maintenance rather than tracked here.

## Phases

### Phase 1 — Lint / format / type-check baseline (HP4, HP5)

**Goal:** `uv run ruff check .`, `uv run ruff format --check .`, and `uv run mypy
tests/` all pass on a clean checkout. CLAUDE.md commands honor their promise.

**Test (write first):** new file `tests/validate_tooling.py` runs each of the
three commands as a subprocess against the repo and asserts exit code 0.

**Changes:**
- `pyproject.toml`: add `types-PyYAML` to dev group; add `[tool.ruff]` and
  `[tool.mypy]` config blocks documenting line length, target version, strict
  flag.
- Remove unused `import os` from `tests/conftest.py`.
- Remove unused `import pytest` from `tests/validate_links.py`,
  `tests/validate_markdown.py`, `tests/validate_yaml.py`.
- Run `ruff format` to fix the three flagged files.

**Definition of done:** `validate_tooling.py` passes; existing 55 tests still
pass; `uv run ruff check .` exits 0.

### Phase 2 — CI workflow hardening (M6, M7) + add lint gate

**Goal:** `.github/workflows/test.yml` has explicit `permissions:`,
`concurrency:`, `timeout-minutes:`; CI runs `ruff check` and
`ruff format --check` alongside pytest; actions are pinned to commit SHAs.

**Test (write first):** extend `tests/validate_tooling.py` (or new
`tests/validate_ci.py`) with checks that parse the workflow YAML and assert:
- top-level `permissions:` exists with `contents: read`.
- top-level `concurrency:` block present.
- the `test` job has `timeout-minutes` set (numeric, > 0).
- `ruff check` and `ruff format --check` appear as steps.
- `actions/checkout` and `astral-sh/setup-uv` use full 40-char SHAs (regex).

**Changes:** edit `.github/workflows/test.yml`:
- Add `permissions: contents: read`.
- Add `concurrency: group: ${{ github.workflow }}-${{ github.ref }}, cancel-in-progress: true`.
- Add `timeout-minutes: 10` on the job.
- Pin `actions/checkout@v6` → `actions/checkout@<sha> # v6.x.x` and same for
  `astral-sh/setup-uv@v8.0.0`.
- Add steps: `uv run ruff check .` and `uv run ruff format --check .`.

**Definition of done:** new validator passes; workflow YAML parses; pytest still
55+ green.

### Phase 3 — `mcp-server.yaml` image (HP1) — BLOCKED on open question

**Goal:** the manifest references a real, tagged, pull-able image and matches
the project's "no `:latest` for tagged images" rule.

**Test (write first):** new check in `tests/validate_yaml.py` (or new file)
that walks every container image in every manifest and asserts no `:latest`
suffix appears.

**Changes:** depend on Michael's decision in the open question above. If (1):
update `image:` to `ghcr.io/kagent-dev/kagent/tools:0.1.4`. If (2): replace
with `ghcr.io/containers/kubernetes-mcp-server:<verified-tag>`. If (3): leave
image but add a `# This image path is illustrative; kagent ships ...` comment
and skip the no-`:latest` test for this file with a documented exclusion.

**Definition of done:** new image-tag validator passes; manifest YAML still
parses; image reference matches a verified upstream artifact (or is documented
as illustrative).

### Phase 4 — Knative version drift (HP2)

**Goal:** Lab 04's Knative install pins reflect a current Knative Serving
release; the doc one-pager either pins a version or uniformly defers.

**Test (write first):** new test in `tests/validate_factchecks.py`
(`TestKnativeVersion`) asserting:
- No reference to `knative-v1.17.0` outside of changelog/correction context.
- Lab 04 README references `knative-v1.21` or higher.

**Changes:**
- `labs/04-kserve-inference/README.md`: replace all `knative-v1.17.0` with
  `knative-v1.21.2` (Step 1 install URLs and Clean up section).
- Verify the URLs return 200 manually before committing (the test cannot do
  network checks in CI; verification is local).

**Definition of done:** new fact-check passes; existing fact-check tests still
pass; lab text reads coherently.

### Phase 5 — KServe v0.17.0 server-side path (HP3)

**Goal:** Lab 04 offers v0.17.0 as the recommended path with `--server-side`,
keeping v0.14.1 as a documented fallback for `kubectl apply` simplicity.

**Test (write first):** assertion in fact-check tests that the lab README
mentions `--server-side` AND `v0.17.0` as a current option (so future drift
breaks loudly).

**Changes:** edit `labs/04-kserve-inference/README.md` Step 1 to present:
- Recommended: `kubectl apply --server-side -f .../v0.17.0/kserve.yaml`
- Alternative for older kubectl: `kubectl apply -f .../v0.14.1/...` with
  rationale unchanged.

**Definition of done:** new test passes; lab still reads clearly.

### Phase 6 — Lab 02 DRA example driver path correction (M14)

**Goal:** Part B references the canonical upstream
(`kubernetes-sigs/dra-example-driver`) with a working install path.

**Test (write first):** `tests/validate_factchecks.py` adds
`TestDRADriverPath` asserting:
- No references to `kubernetes/test/e2e/dra/test-driver`.
- If `dra-example-driver` is mentioned, it points to `kubernetes-sigs/...`.

**Changes:** rewrite `labs/02-dra-resource-claims/README.md` Part B Step 1-2 to
use the Helm install command from the kubernetes-sigs repo. Update Clean up
accordingly.

**Definition of done:** new test passes; reader can follow Part B against real
upstream artifacts.

### Phase 7 — Imperative → declarative `kubectl create namespace` (M9)

**Goal:** lab READMEs and manifests use `kubectl apply -f` for namespaces,
matching the rest of each lab's declarative style.

**Test (write first):** `tests/validate_factchecks.py` (or new) asserts no
`kubectl create namespace` lines remain in lab READMEs (allowed in optional/
cloud labs where rationale differs).

**Changes:**
- Add a small `namespace.yaml` per affected lab (01, 04, 06).
- Update README steps to `kubectl apply -f manifests/namespace.yaml`.

**Definition of done:** test passes; manifests work end-to-end.

### Phase 8 — `securityContext` teaching pattern (M8)

**Goal:** at least one job manifest demonstrates pod-level
`securityContext` (`runAsNonRoot`, `seccompProfile`, dropped capabilities,
`readOnlyRootFilesystem`) and the corresponding lab README explains it.

**Test (write first):** a check that `labs/01-kueue-basics/manifests/sample-job.yaml`
contains a `securityContext:` block with `runAsNonRoot: true`. (Bound to one
file only — we are not retrofitting every manifest in a content repo, just
demonstrating the pattern.)

**Changes:**
- Pick `labs/01-kueue-basics/manifests/sample-job.yaml` (busybox runs as root
  by default — natural teaching example).
- Add `securityContext` at pod and container level. Use `busybox:1.36-glibc`
  if needed for nonroot compatibility, or comment the pod-level user.
- Update Lab 01 README "What just happened?" with a short paragraph on
  `securityContext`.

**Definition of done:** test passes; lab manifest still runs (verified against
local kind cluster if available; otherwise documented as not yet runtime-verified).

### Phase 9 — PROJECT_STATE.md update

**Goal:** PROJECT_STATE.md reflects the work done above.

**Test:** none — content state file.

**Changes:** rewrite PROJECT_STATE.md with the phases completed, branch
status, and next steps.

**Definition of done:** PROJECT_STATE.md is accurate and dated.

## Out of scope (deferred to follow-up issues)

- Markdownlint / shellcheck CI integration (M12, M13).
- Standardized cleanup sections per lab (L22).
- Helm chart digest pinning (L21).
- `.editorconfig`, PR/issue templates (L20, L24).
- One-pager Knative version pin (L16).
- Tighter `_strip_code_blocks` regex (M11).
- Nightly external-URL validation job (M15).
- `requires-python` floor revision (L18).

These are tracked here for visibility; they do not block this plan.
