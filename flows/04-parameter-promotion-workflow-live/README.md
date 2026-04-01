# 04 Parameter Promotion Workflow (Live)

This flow step covers how the live system consumes promoted strategy / parameter / instruction updates.

## Responsibility

- store and read the active strategy pointer
- publish a new active pointer version
- detect active version changes in the daemon
- emit upgrade requests
- process upgrade requests out-of-band
- run the unified `strategy_upgrade_event`

## Current contents

### pointer
- `pointer/strategy_pointer.py`

### promotion
- `promotion/promote_strategy.py`

### upgrade
- `upgrade/process_strategy_upgrade_request.py`
- `upgrade/strategy_upgrade_event.py`

### legacy-substeps
- `legacy-substeps/review_event.py`
- `legacy-substeps/calibrate_event.py`

## Notes on current cleanup

This flow step has already been cleaned to remove old `crypto-trading` runtime log paths from the migrated pointer/request scripts.

## Likely next additions

- request/result dedupe helpers
- handover marker/state helpers if they split out further
- more explicit strategy-pointer validation / schema helpers

## Expected future home

These files will likely split between final `src/runtime/`, `src/state/`, and `src/runners/` areas inside `quantitative-trading`.
