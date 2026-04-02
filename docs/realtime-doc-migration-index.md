# Realtime Doc Migration Index

This docs tree was seeded from realtime/live-operation material previously living in the older hybrid repository.

## Migrated as core realtime docs
- `02-runtime-and-modes.md`
- `09-execution-artifacts.md`
- `05-review-operations.md`
- `06-review-architecture.md`
- `03-environment-and-operations.md`
- `07-regime-and-decision-flow.md`
- `08-state-and-artifacts.md`

## Split from hybrid docs
- `04-parameter-promotion-workflow-live.md`
- `10-research-runtime-separation-live.md`

## Next step

Use these docs to derive the first wave of code/script migration into `quantitative-trading`.

## Current implementation checkpoint

The repo is now runnable in isolation and the dummy live-side E2E path is materially proven:

- repo-local bootstrap exists: `pyproject.toml`, `requirements.txt`, `.venv`
- execution/runtime smoke tests run successfully inside the repo
- durable upgrade detection across daemon restarts now exists
- stale dead-code remnants such as `src/review/compare.py` and `src/runtime/regime_runner_legacy_runner_import.py` have been removed

So the immediate code migration priority is now:
1. simplify `src/execution_cycle.py`
2. keep pruning stale compatibility layers
3. align docs with the settled `src/` runtime paths
