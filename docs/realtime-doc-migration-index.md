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

The repo now has enough migrated `src/` code to attempt the dummy live-side E2E path, but it is not yet self-bootstrapable or cleanly converged:

- there is still no Python dependency manifest in the repo, so direct smoke tests currently fail on missing packages such as `python-dotenv`
- `src/execution_cycle.py` has been substantially cleaned up; remaining work is mostly final artifact/documentation sweep rather than old compare / shadow-plan / router-composite removal
- `src/runtime/trade_daemon.py` still partially assumes the older execution summary shape

So the immediate code migration priority is:
1. make the repo runnable in isolation
2. make the dummy execution artifact path work end to end
3. then continue deleting stale compatibility layers
