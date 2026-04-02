# 11 Dummy Strategy E2E Plan

This document defines the planned end-to-end validation path for a dummy strategy / dummy promoted live version.

Purpose:
- verify the current `quantitative-trading` target architecture with the smallest possible live-side flow
- reveal which scripts/modules are still truly required
- reveal which modules are only historical leftovers or stale compatibility shims

## Test philosophy

Do **not** delete old or duplicated files just because they look legacy.

Instead:
1. define the smallest realistic live path
2. run it with a dummy promoted version
3. observe which modules are actually exercised
4. only then delete what is proven unused

## Minimal target flow

### Step A — promote a dummy active version
Use the live-side promotion entrypoint to write a dummy active strategy pointer.

Target modules:
- `src/upgrade/strategy_pointer.py`
- `src/upgrade/promote_strategy.py`

Expected artifacts:
- `logs/runtime/active-strategy.json`

## Step B — run a bounded trade-daemon cycle
Run the daemon for a bounded cycle with the dummy active version in place.

Target modules:
- `src/runtime/trade_daemon.py`
- `src/runtime/mode.py`
- `src/runtime/mode_policy.py`
- `src/runtime/workflows.py`
- `src/execution/pipeline.py`
- `src/execution/controller.py`
- `src/state/store.py`
- `src/state/live_position.py`

Expected artifacts:
- `logs/runtime/latest-execution-cycle.json`
- possibly `logs/runtime/execution-cycles/*.jsonl`
- `logs/runtime/trade-daemon-*.jsonl`

## Step C — trigger an upgrade change
Promote a second dummy version so the daemon detects an active version change.

Expected artifacts/events:
- daemon detects strategy hot swap
- daemon emits `strategy_upgrade_event_requested`
- daemon writes `logs/runtime/latest-strategy-upgrade-request.json`

Primary target modules:
- `src/upgrade/promote_strategy.py`
- `src/runtime/trade_daemon.py`
- `src/upgrade/strategy_pointer.py`

## Step D — process the upgrade request out-of-band
Run the upgrade request consumer.

Target modules:
- `src/upgrade/process_strategy_upgrade_request.py`
- `src/upgrade/strategy_upgrade_event.py`
- `src/runtime/workflows.py`

Expected artifacts:
- `logs/runtime/latest-strategy-upgrade-result.json`
- `logs/runtime/latest-strategy-handover-marker.json`

## Step E — validate review/export side
Use the generated artifacts to confirm the review path can at least ingest and summarize the relevant runtime data.

Target modules:
- `src/review/ingestion.py`
- `src/review/aggregator.py`
- `src/review/performance.py`
- `src/review/report.py`
- `src/review/export.py`

## Current highest-risk mismatch areas

These are the places most likely to still reflect the old hybrid design and therefore most likely to break or prove unnecessary during the dummy run.

### 1. Old import paths still point at `src.runners.*`
Many copied modules still import from old runner/runtime paths from the source repo.
These imports must be audited as we move from `flows/` into the final `src/` package layout.

### 2. Old multi-account assumptions remain in tests and pipeline helpers
Current tests in the old repo still heavily reflect old runner names and old multi-account assumptions.
The dummy path should help identify which of those are irrelevant to the new architecture where the live side trades only the currently promoted historical-side model/version.

### 3. Regime runner role may be oversized
`regime_runner.py` still needs validation against the current design philosophy.
It may remain a live input bridge, or it may shrink further.

### 4. Legacy compatibility substeps may prove redundant
- `review_event.py`

These may survive only as internal upgrade-event helpers, or may become deletable after the unified path is proven.

## Likely deletion candidates after successful dummy run

Only candidates — not auto-delete yet.

- isolated legacy compare/review helpers that are never touched by the dummy path
- isolated legacy state models that remain unreferenced
- compatibility wrappers that duplicate the final unified upgrade path
- old flow copies once the final `src/` package path is proven stable

## Current dummy live-cycle implementation

A deterministic dummy mode now exists in `src/runtime/dummy_cycle.py` and is wired into `src/runtime/trade_daemon.py` via `--dummy-live-cycle`.

Behavior:
- `dummy-v1` (or versions without the upgraded marker) uses a 5-second cadence
  - buy/enter
  - hold about 5 seconds
  - sell/exit
  - hold about 5 seconds
  - repeat
- `dummy-v2` / upgraded versions use a 3-second cadence
  - buy/enter
  - hold about 3 seconds
  - sell/exit
  - hold about 3 seconds
  - repeat

This mode also injects dummy fee/pnl/funding fields so `theoretical_snapshot`, `execution_drag_proxy_usdt`, and review-side execution deviation reporting have non-placeholder data to consume during dummy trading cycles.

## Current success criteria

A successful dummy strategy validation should prove:

1. dummy promotion writes active pointer
2. trade daemon reads current pointer without restart
3. bounded execution cycle writes execution artifact
4. version change produces upgrade request artifact
5. out-of-band consumer produces upgrade result + handover marker
6. review side can consume the resulting runtime artifacts
7. after this pass, we can confidently identify true dead files

## Current verified status

Already verified in `quantitative-trading`:
- repo-local bootstrap files exist: `pyproject.toml`, `requirements.txt`, `.venv`
- `logs/runtime/active-model-inputs.json` is now required in practice and a minimal seed bundle is sufficient to unblock repo-local runtime smoke tests
- `Settings` now accepts runtime-attached extra fields, so `BtcRegimeRunner` can attach `model_inputs` without crashing
- `.venv/bin/python -m src.execution_cycle` runs successfully again
- bounded `.venv/bin/python -m src.runtime.trade_daemon --dummy-live-cycle --interval-seconds 1 --max-cycles N` runs successfully and writes:
  - `logs/runtime/latest-execution-cycle.json`
  - `logs/runtime/execution-cycles/*.jsonl`
  - `logs/runtime/trade-daemon/*.jsonl`
- dummy execution artifacts now contain non-placeholder fee/pnl driven theoretical snapshot fields during enter/exit cycles
- dummy promotion writes active pointer for `dummy-v1` and `dummy-v2`

Still not yet verified / still mismatched:
- upgrade request emission is currently only reliable when the version change happens while the same daemon process is still alive
- if promotion happens between separate daemon runs, `latest-strategy-upgrade-request.json` is not emitted because `trade_daemon` only tracks `previous_strategy_version` in memory
- therefore the full Step C → Step D chain is **not yet durably complete** across restarts

## Immediate architecture implication

Upgrade detection must move from ephemeral in-process state to a durable runtime artifact.

Recommended fix:
- persist a last-seen active strategy version marker under `logs/runtime/`
- compare current pointer vs last-seen/last-processed marker on each daemon cycle
- emit `latest-strategy-upgrade-request.json` whenever an unprocessed version change is discovered, even after daemon restart

Only after that change should the dummy-v1 → dummy-v2 handover path be treated as fully verified.
