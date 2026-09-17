# Project State: cloud-native-ai-lab

Phase: 3.3 Promote (complete)
Approved: 2026-04-26 by Michael, conversational approval of docs/improvement-plan.md. No sha256 seal exists; this work predates contract sealing in this repo. See Contracts.

## Lifecycle
- [x] 1.1 Research
- [x] 1.2 Plan
- [x] 1.3 Approve
- [x] 2.1 Test
- [x] 2.2 Implement
- [x] 2.3 Verify
- [x] 3.1 Stage
- [x] 3.2 Confirm CI
- [x] 3.3 Promote

## Contracts

No sealed contract with a sha256 hash exists for this repo. The written plan is
`docs/improvement-plan.md`, approved conversationally on 2026-04-26 ("create a
plan, write it to docs, tdd and test it first then go for it phase by phase").
Recording it as `pending` would misrepresent shipped and promoted work, so it is
recorded here as an unsealed approval instead. Future plans in this repo should
seal properly via `/prd`.

**Date:** 2026-09-17
**Branch:** staging. `main` and `staging` are identical at `ca35133`; working tree clean, nothing unpushed.
**Repo:** [peopleforrester/cloud-native-ai-lab](https://github.com/peopleforrester/cloud-native-ai-lab), public, Apache 2.0, release `v1.0.0`.
**Plan:** [docs/improvement-plan.md](docs/improvement-plan.md)

**Verification method:** TDD throughout. Version-gating tests were updated first
(red), then content edited to green. Every upstream version was checked against
the project's live GitHub releases on the date claimed, never from training
data, and release-asset URLs were confirmed reachable. **No lab has been
executed end to end against a live kind cluster.** Manifests parse and install
URLs resolve; behaviour on a running cluster is unverified.

## Current status

| Check | State |
|---|---|
| Tests | 74 passing across 9 validator modules |
| Lint, format, types | `ruff check`, `ruff format --check`, `mypy tests/` all green |
| CI on `main` | success |
| Open issues | 0 |
| Open pull requests | 0 |
| Dependabot alerts | 0 |
| repo-showcase checker | clean, exit 0 |

Python 3.12.13, pinned via `.python-version`. Toolchain at mypy 2.3, pytest
9.1.1, ruff 0.16.8. CI actions SHA-pinned: `actions/checkout` v7.0.1,
`astral-sh/setup-uv` v10.1.0.

## Upstream pins, current

Last full re-verification 2026-09-17. Three refreshes have run since April, at
roughly seven, three and nine week intervals.

| Project | Pin |
|---|---|
| Kueue (lab 01 Helm) | 0.19.4 |
| JobSet (lab 03) | v0.12.0 |
| KServe (lab 04) | v0.20.0 |
| Knative Serving, net-kourier (lab 04) | knative-v1.23.0 |
| LeaderWorkerSet (docs) | v0.10.0 |
| llm-d (docs) | v0.9.0 |
| kagent tools image (lab 06) | 0.2.1 |
| kind, kindest/node (lab 00) | v0.33.0, v1.37.0 (digest-pinned) |
| MCP spec | 2026-07-28 |
| Gateway API Inference Extension | v1.6.1 |

## Work completed since the July refresh

**Showcase pass (August).** The repo went from "written for the people who were
there" to something a stranger can evaluate:

- 16:9 hero at `assets/hero.jpg` with the author portrait composited, cropped to
  head and shoulders. A social preview card is committed beside it at
  `assets/social-card.jpg`, 1280x640 and 131KB, because GitHub crops the card to
  2:1 rather than the hero's 16:9 and enforces a hard 1MB ceiling.
- First screen rebuilt: one-line hook, CI and licence badges backed by real
  artifacts, and a what-you-get table whose every number traces to something
  committed (7 labs, 3-node kind cluster, 74 CI-gated tests, 11 one-pagers).
- The talk is framed as delivered on 24 March 2026 at the RAI in Amsterdam,
  verified against CNCF's published dates for KubeCon EU 2026.

**Truthfulness corrections.** Two defects were introduced by earlier version
sweeps and are now fixed:

- `docs/talk-outline.md` had been swept to claim KServe v0.19.0, a June release,
  inside a script delivered in March, contradicting the v0.17.0 four lines above
  it. It is now frozen as the script as delivered, with a dated note saying its
  versions are deliberately not maintained, because the document is evidence of
  what was said on a particular day rather than a living reference.
- The README claimed all eleven one-pagers were re-verified when six still
  carried March dates. Five were genuinely re-verified and stamped July;
  `aaif.md` was not re-checked and stays at March. The README now claims only
  that each page carries its own verification date.

**Safety.** `transcripts/` was present in the working tree, untracked but not
gitignored, in a public repo, holding material referencing employer work and a
named colleague. Confirmed never tracked and never in git history, so nothing
leaked; now gitignored, and content gates were scoped so they never read
unpublished local files. AI attribution was removed from the README.

**Hygiene.** AGENTS.md is the single real guidance file with CLAUDE.md a
relative symlink to it; `normalize-agents-md.sh` classifies the repo as IDEAL.
`tests/__init__.py` carries its ABOUTME header.

## September 2026 currency sweep

Nine weeks of drift closed. Kueue to 0.19.4, KServe to v0.20.0, Knative and
net-kourier to knative-v1.23.0, LeaderWorkerSet to v0.10.0, llm-d to v0.9.0,
kind to v0.33.0 with the node image at v1.37.0 pinned by digest. Toolchain to
ruff 0.16.8 and mypy 2.3.1, and setup-uv across two majors to v10.1.0.
Kubernetes 1.37.0 is now stable upstream.

Two findings were larger than version numbers:

- **The MCP spec advanced to 2026-07-28**, which removes the `initialize`
  handshake and session header in favour of a stateless core, replaces
  server-initiated calls with multi round-trip requests, and deprecates
  Sampling, Roots and Logging. The one-pager now says what changed rather than
  only carrying a new date.
- **Lab 05's InferenceObjective manifest was never valid.** It declared a kind
  under an apiVersion no GAIE release has ever served, with the field set of a
  different, retired CRD. Corrected against the llm-d-router CRD and gated by
  two new tests. Full reasoning in `decisions.md`.

## Outbound cross-repo requests

- **[mrf-engagement-orchestrator#57](https://github.com/peopleforrester/mrf-engagement-orchestrator/issues/57)**:
  article "The version sweep that rewrote a talk I had already given", drafted
  from this repo's commits and handed over for publishing to
  michaelrishiforrester.com and social fan-out. That repo owns the Micropub
  path; this one owns the evidence. Expect the published URL back as a comment
  on that issue.
- **[KCD_Texas_2026_Workshop#23](https://github.com/peopleforrester/KCD_Texas_2026_Workshop/issues/23)**:
  refresh that repo's PROJECT_STATE.md and create its decisions.md, handed over
  rather than committed directly. Its state file is already on the lifecycle
  schema, so it needs a body refresh, not a migration. The issue carries the
  current facts so nothing has to be re-derived.
- **[mrf-engagement-orchestrator#75](https://github.com/peopleforrester/mrf-engagement-orchestrator/issues/75)**:
  commented to confirm this repo is showcase-ready for the public Projects page,
  including the warning about the untracked-but-unignored directory, which is
  worth checking across the rest of the showcase set.

## Outstanding

Nothing is blocked on code. What remains needs a person:

1. **Social preview card upload.** Manual, no `gh` command exists. Settings then
   General then Social preview, using `assets/social-card.jpg`. Until it is
   done, a link to this repo renders a grey GitHub avatar rather than the card.
2. **LinkedIn post.** Drafted and scanned clean, not posted. Copy and banner are
   in the LinkedIn drop on Megumi with instructions in
   `Cloud-Native-AI-Lab-notes.txt`.
3. **Article publication**, tracked on orchestrator#57.

## Known limits, carried forward

- **No live-cluster validation.** Every refresh has crossed minor boundaries
  without a cluster run. The September one matters most: Kueue 0.19 enables
  `WaitForPodsReady` by default with a 30 minute timeout, which changes what
  admission means on a slow cluster, and that is documented in lab 01 rather
  than observed. llm-d sits on the v0.7 line's breaking changes (NVIDIA driver
  580 or newer, standalone default mode), noted in its one-pager but not
  exercised.
- **`docs/projects/aaif.md` is still dated March 2026.** It was not re-verified
  and was deliberately not stamped.
- **Version pins in teaching content drift every six to eight weeks.** Two
  refreshes inside four weeks is the observed rate. The scheduled 30-day
  check-in routine (`trig_01PwZGVCYdzFVDCUqNFWo9JL`) is the backstop; a periodic
  sweep is the standing cost of pinning exact versions in long-lived content.

## Out of scope (carried forward)

markdownlint and shellcheck in CI, standardized per-lab cleanup sections, Helm
chart digest pinning, `.editorconfig`, PR and issue templates, a nightly
external-URL validation job, `requires-python` floor revision. See
`docs/improvement-plan.md`.
