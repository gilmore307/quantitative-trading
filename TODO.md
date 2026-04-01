# TODO

## Current focus
- make the dummy strategy E2E path actually runnable in `quantitative-trading`
- converge runtime artifacts on a single active-strategy / single-account live path
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
5. only after the dummy path is proven, continue deleting stale review/compare/shadow-plan compatibility code

## Known blockers
- repo currently has no `pyproject.toml` / `requirements.txt`, so even basic execution currently fails on missing deps such as `python-dotenv`
- `src/execution_cycle.py` still carries legacy compare / shadow-plan / router-composite oriented logic
- `src/runtime/trade_daemon.py` still reads old summary fields that do not match the new active-strategy artifact shape cleanly

## Notes
- docs-first migration rule still stands: keep project docs updated as the code path is clarified
- dummy E2E remains the deletion gate for old files/modules
