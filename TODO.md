# TODO

## Current focus
- make the dummy strategy E2E path actually runnable in `quantitative-trading`
- converge runtime artifacts on a single active-strategy / single-account live path
- enforce the architecture rule that **only the model/version promoted from the historical backtest side is traded live**
- remove stale parallel / compare / router-composite compatibility layers only where the dummy path proves they are not needed

## Immediate next actions
1. keep the repo-local bootstrap path clean and executable for direct smoke tests
2. keep `.venv/bin/python -m src.execution_cycle` and bounded `trade_daemon` runnable in a clean environment
3. simplify `src/execution_cycle.py` so its active-strategy artifact path does not depend on legacy compare/router-composite summary fields
4. re-run the dummy bounded daemon flow and verify these artifacts:
   - `logs/runtime/active-strategy.json`
   - `logs/runtime/latest-execution-cycle.json`
   - `logs/runtime/execution-cycles/*.jsonl`
   - `logs/runtime/trade-daemon-*.jsonl`
5. validate `theoretical_snapshot` / execution-drag fields on a cycle that actually contains fill/fee/pnl data
   - dummy live-cycle mode now exists:
     - `dummy-v1` => enter, hold ~5s, exit, hold ~5s, repeat
     - `dummy-v2` => enter, hold ~3s, exit, hold ~3s, repeat
   - invocation: `.venv/bin/python -m src.runtime.trade_daemon --dummy-live-cycle --interval-seconds 1 --max-cycles N`
6. make upgrade detection durable across daemon restarts, not only within a single daemon process
   - current `trade_daemon` only compares `previous_strategy_version` in-memory
   - if the daemon restarts between promotions, `latest-strategy-upgrade-request.json` is never emitted
   - persist last-seen strategy version / processed-upgrade marker under `logs/runtime/` and emit request whenever an unprocessed version change is detected
7. after durable upgrade detection exists, re-run dummy-v1 → dummy-v2 and verify:
   - `logs/runtime/latest-strategy-upgrade-request.json`
   - `logs/runtime/latest-strategy-upgrade-result.json`
   - `logs/runtime/latest-strategy-handover-marker.json`
8. continue deleting stale review/compare/shadow-plan compatibility code and family-account config residue from `src/`
9. keep `src/` as the only authoritative code tree; do not reintroduce a parallel migration code tree

## Known blockers
- `src/execution_cycle.py` still carries legacy compare / shadow-plan / router-composite oriented logic
- `src/runtime/trade_daemon.py` still relies on in-process `previous_strategy_version` tracking, so upgrade request emission is not durable across daemon restarts

## Notes
- docs-first migration rule still stands: keep project docs updated as the code path is clarified
- repo-local bootstrap is now present: `pyproject.toml`, `requirements.txt`, `.venv`
- smoke test artifact bundle now also requires `logs/runtime/active-model-inputs.json`; a minimal seed file has been added for repo-local execution
- `.venv/bin/python -m src.execution_cycle` now runs successfully again (current artifact lands in develop-mode hold path)
- bounded `.venv/bin/python -m src.runtime.trade_daemon --dummy-live-cycle --interval-seconds 1 --max-cycles N` now runs successfully and writes runtime execution artifacts
- upgrade-request emission is still incomplete across daemon restarts because version-change detection is currently in-memory only
- dummy E2E remains the deletion gate for old files/modules
- strategy family names such as `trend` / `meanrev` / `compression` / `crowded` / `realtime` are historical-side taxonomy labels, not the intended steady-state live account roster for this repo
- the live side should be modeled around the currently promoted active strategy/model pointer, not around a standing multi-family live-account matrix
