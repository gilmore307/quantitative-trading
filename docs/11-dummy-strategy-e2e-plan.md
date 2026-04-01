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
- dummy promotion writes active pointer
- daemon detects live hot-swap from `dummy-v1` to `dummy-v2`
- daemon emits `strategy_upgrade_event_requested`
- daemon changes dummy execution cadence from 5 seconds to 3 seconds after promotion
- out-of-band consumer writes:
  - `logs/runtime/latest-strategy-upgrade-result.json`
  - `logs/runtime/latest-strategy-handover-marker.json`

Remaining mismatch still visible after this validation:
- configuration/test helpers still contain legacy family/account naming in some places, but upgrade workflow internals no longer perform the old calibrate-style multi-account bucket/account reset path
