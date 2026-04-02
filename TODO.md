# TODO

## Current focus
- make the dummy strategy E2E path actually runnable in `quantitative-trading`
- converge runtime artifacts on a single active-strategy / single-account live path
- enforce the architecture rule that **only the model/version promoted from the historical backtest side is traded live**
- remove stale parallel / compare / router-composite compatibility layers only where the dummy path proves they are not needed

## Immediate next actions
1. simplify `src/execution_cycle.py` so its active-strategy artifact path does not depend on legacy compare/router-composite summary fields
2. review the remaining runtime / review path now that dummy E2E artifacts are available end-to-end
3. validate `theoretical_snapshot` / execution-drag fields on additional enter/exit cycles, not just a minimal bounded smoke run
4. continue deleting stale review/compare/shadow-plan compatibility code and family-account config residue from `src/`
5. keep `src/` as the only authoritative code tree; do not reintroduce a parallel migration code tree

## Verified now
- repo-local bootstrap is present and usable: `pyproject.toml`, `requirements.txt`, `.venv`
- `logs/runtime/active-model-inputs.json` exists and unblocks repo-local runtime smoke tests
- `.venv/bin/python -m src.execution_cycle` runs successfully again
- bounded `.venv/bin/python -m src.runtime.trade_daemon --dummy-live-cycle --interval-seconds 1 --max-cycles N` runs successfully and writes:
  - `logs/runtime/latest-execution-cycle.json`
  - `logs/runtime/execution-cycles/*.jsonl`
  - `logs/runtime/trade-daemon/*.jsonl`
- dummy execution artifacts include fee/pnl-driven `theoretical_snapshot` / `execution_drag_proxy_usdt` fields
- promotion path works for `dummy-v1` and `dummy-v2`
- durable upgrade detection across daemon restarts now works via `logs/runtime/strategy-upgrade-state.json`
- dummy-v1 → dummy-v2 now produces:
  - `logs/runtime/latest-strategy-upgrade-request.json`
  - `logs/runtime/latest-strategy-upgrade-result.json`
  - `logs/runtime/latest-strategy-handover-marker.json`
- out-of-band upgrade consumer runs successfully and also emits a review artifact bundle under `reports/trade-review/`

## Known blockers
- `src/execution_cycle.py` still carries legacy compare / shadow-plan / router-composite oriented logic
- docs and code still contain some historical naming / migration residue that should now be pruned based on the proven dummy E2E path

## Notes
- docs-first migration rule still stands: keep project docs updated as the code path is clarified
- dummy E2E is now materially proven as a runnable repo-local validation path
- strategy family names such as `trend` / `meanrev` / `compression` / `crowded` / `realtime` are historical-side taxonomy labels, not the intended steady-state live account roster for this repo
- the live side should be modeled around the currently promoted active strategy/model pointer, not around a standing multi-family live-account matrix
