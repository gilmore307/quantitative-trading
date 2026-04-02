# TODO

## Current focus
- keep the dummy strategy E2E path runnable in `quantitative-trading`
- converge runtime artifacts on a single active-strategy / single-account live path
- enforce the architecture rule that **only the model/version promoted from the historical backtest side is traded live**
- remove stale parallel / compare / router-composite compatibility layers only where the dummy path proves they are not needed
- preserve potentially valuable runtime statistics until report / dashboard requirements are settled

## Immediate next actions
1. simplify `src/execution_cycle.py` structurally without prematurely deleting potentially useful report/stat fields
2. enhance `src/review/report.py` and export output to consume the retained runtime statistics more explicitly
3. review the remaining runtime / review path now that dummy E2E artifacts are available end-to-end
4. continue deleting stale compatibility code and path residue that is clearly broken or unused
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
- stale dead-code remnants removed and kept removed:
  - `src/review/compare.py`
  - `src/runtime/regime_runner_legacy_runner_import.py`
- ops readers now align with current repo + artifact structure:
  - `src/ops/trade_alert_watcher.py`
  - `src/ops/discord_notifier.py`
- top-level `latest-execution-cycle.json` structure is slimmer, while potentially valuable runtime summary statistics have been restored for future reporting use

## Current artifact policy
- authoritative runtime artifact/schema reference lives in `docs/12-runtime-data-contract.md`
- keep potentially valuable runtime statistics in `result.summary` until report/dashboard requirements are stable
- remove only:
  - clearly broken old-architecture leftovers
  - dead modules with no references
  - pure mirror layers that add no information
- do not prematurely optimize artifact thinness at the cost of losing future reporting signal

## Known blockers
- `src/execution_cycle.py` still carries structural complexity and can be simplified further
- docs and code still contain some historical naming / migration residue that should continue to be pruned
- report/export layers do not yet fully exploit the retained runtime statistics

## Notes
- docs-first migration rule still stands: keep project docs updated as the code path is clarified
- dummy E2E is now materially proven as a runnable repo-local validation path
- strategy family names such as `trend` / `meanrev` / `compression` / `crowded` / `realtime` are historical-side taxonomy labels, not the intended steady-state live account roster for this repo
- the live side should be modeled around the currently promoted active strategy/model pointer, not around a standing multi-family live-account matrix
