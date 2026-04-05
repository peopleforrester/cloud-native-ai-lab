# Project State: Senior Review Remediation

**Date:** 2026-04-06
**Branch:** staging
**Review Grade:** B+ → A (all items addressed)
**Status:** Complete

## Action Plan (all done)

### Phase 1: Project Tooling
- [x] Add `[project]` section to `pyproject.toml`
- [x] Add `ruff` and `mypy` to dev dependencies
- [x] Add `.python-version` file pinning 3.12
- [x] Run `uv sync --dev` to generate `uv.lock`

### Phase 2: Fix CLAUDE.md and scripts
- [x] Fix `mypy src/` → `mypy tests/` in CLAUDE.md
- [x] Rewrite `scripts/test.sh` to use `uv run pytest`
- [x] Remove legacy `requirements-dev.txt`

### Phase 3: Content Fixes
- [x] Update AKS K8s version from 1.31 to 1.35
- [x] Fix llm-d attribution: "Launched by Red Hat" not "Co-built"
- [x] Update Gateway API Inference Extension to GA API (`inference.networking.k8s.io/v1`)
- [x] Fix Lab 05 step ordering: gateway (with namespace) applied before pool/objective

### Phase 4: CI Pipeline
- [x] Add `.github/workflows/test.yml`

### Phase 5: Verify
- [x] All 55 tests pass
