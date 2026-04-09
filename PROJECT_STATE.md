# Project State: Senior Review + Recency Remediation

**Date:** 2026-04-06
**Branch:** main (clean)
**Status:** Complete — all items addressed across two commits

## Commit 1: Senior Review Fixes (93c193d)
- [x] `pyproject.toml` — added `[project]` section, ruff/mypy dev deps
- [x] `.python-version` — pinned 3.12
- [x] `uv.lock` — committed for reproducible builds
- [x] `scripts/test.sh` — rewritten to use uv; removed `requirements-dev.txt`
- [x] `CLAUDE.md` — fixed mypy target to `tests/`
- [x] Gateway API Inference Extension → GA `inference.networking.k8s.io/v1`
- [x] Lab 05 step ordering — namespace before pool/objective
- [x] llm-d attribution — "Launched by Red Hat"
- [x] AKS K8s version → 1.35
- [x] GitHub Actions CI workflow added

## Commit 2: April 2026 Recency Update (e38828c)
- [x] Kueue: 0.16.4 → 0.17.0
- [x] kind: v0.27.0 → v0.31.0
- [x] NVIDIA device plugin: v0.17.0 → v0.17.1
- [x] actions/checkout: v4 → v6
- [x] astral-sh/setup-uv: v5 → v8.0.0

## Verified Current (no update needed)
- KServe v0.17.0 — still latest
- JobSet v0.11.1 — still latest
- LeaderWorkerSet v0.8.0 — still latest
- MCP spec 2025-11-25 — still current
- CNCF survey stats (82% K8s prod, 66% gen AI) — verified accurate
- kindest/node:v1.35.1 — exists on Docker Hub, valid
