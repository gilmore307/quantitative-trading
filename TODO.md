# TODO

## Current focus
- make the dummy strategy E2E path actually runnable in `quantitative-trading`
- converge runtime artifacts on a single active-strategy / single-account live path
- enforce the architecture rule that **only the model/version promoted from the historical backtest side is traded live**
- remove stale parallel / compare / router-composite compatibility layers only where the dummy path proves they are not needed

## Immediate next actions
1. finish the repo-local `.venv` bootstrap path and dependency manifest so the repo can be smoke-tested directly
2. make `.venv/bin/python -m src.execution_cycle` and bounded `trade_daemon` runnable in a clean environment
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
6. next: expose/record upgrade-event behavior while switching from dummy-v1 to dummy-v2 mid-run
   - hot-swap detection + upgrade request emission already verified
   - out-of-band request consumer (`src.upgrade.process_strategy_upgrade_request`) now also runs successfully and writes:
     - `logs/runtime/latest-strategy-upgrade-result.json`
     - `logs/runtime/latest-strategy-handover-marker.json`
7. continue deleting stale review/compare/shadow-plan compatibility code and family-account config residue from `src/`
8. keep `src/` as the only authoritative code tree; do not reintroduce a parallel migration code tree

## Known blockers
- repo currently has no `pyproject.toml` / `requirements.txt`, so even basic execution currently fails on missing deps such as `python-dotenv`
- `src/execution_cycle.py` still carries legacy compare / shadow-plan / router-composite oriented logic
- `src/runtime/trade_daemon.py` still reads old summary fields that do not match the new active-strategy artifact shape cleanly

## Notes
- docs-first migration rule still stands: keep project docs updated as the code path is clarified
- dummy E2E remains the deletion gate for old files/modules
- strategy family names such as `trend` / `meanrev` / `compression` / `crowded` / `realtime` are historical-side taxonomy labels, not the intended steady-state live account roster for this repo
- the live side should be modeled around the currently promoted active strategy/model pointer, not around a standing multi-family live-account matrix
