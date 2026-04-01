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

- `src/runtime/strategy_pointer.py`
- `src/runners/promote_strategy.py`
- `src/runners/process_strategy_upgrade_request.py`
- `src/runners/strategy_upgrade_event.py`
- `src/runners/review_event.py`
- `src/runners/calibrate_event.py`

## Likely next additions

- request/result dedupe helpers
- handover marker/state helpers if they split out further
- more explicit strategy-pointer validation / schema helpers

## Expected future home

These files will likely split between final `src/runtime/`, `src/state/`, and `src/runners/` areas inside `quantitative-trading`.
