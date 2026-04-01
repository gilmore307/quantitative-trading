# Runtime and Modes

## Goal

Document the long-running runtime state model and the event model around strategy upgrades.

## Long-running modes

Only long-lived runtime states should be modeled as modes:

- `develop` — idle development / maintenance mode; do not run normal strategy execution or routing
- `trade` — normal trading mode; the long-running daemon state that executes the current active strategy
- `reset` — development-only destructive reset: flatten, verify flat, convert residual assets if needed, rebuild/reset local bucket state, then return to `develop`
- `test` — dedicated execution-system test mode; does not run normal strategy logic and should return to `develop`

## Events / jobs

These are not long-running modes.
They are events/jobs that happen around the always-on trade daemon.

- `strategy_upgrade_event` — the canonical promotion-triggered upgrade event
- `review` — upgrade validation / execution diagnosis sub-step
- `calibrate` — deprecated legacy label; not part of the default strategy-upgrade flow anymore

## Core runtime interpretation

### Trade daemon

`trade` is the only normal always-on live-trading state.

The daemon should:
- keep running continuously
- keep reading the current active strategy pointer
- detect active strategy version changes without requiring a restart
- continue trading with the new active strategy version once detected
- emit upgrade-related request artifacts out-of-band instead of blocking the main loop

### Review / calibrate are not modes

`review` and `calibrate` should no longer be treated as standalone runtime modes.

They are now best understood as:
- compatibility labels
- helper/event concepts

Only `review` remains part of the default `strategy_upgrade_event` flow. `calibrate` is deprecated for strategy switching because strategy performance is measured from segment-start account state to segment-end account state rather than by forcing a reset baseline.

## Strategy hot-swap model

The intended runtime model is:

1. historical research promotes a new strategy/parameter version
2. active strategy pointer is updated
3. trade daemon detects the new active version while staying alive
4. daemon continues trading with the new version
5. daemon emits a `strategy_upgrade_event_requested` signal for out-of-band validation / helper work

This is a hot-swap model, not a stop-the-world mode-switch model.

## Position handling during upgrade

If an upgrade happens while a position is open:
- do not force an upgrade-only flatten just to make the transition look clean
- handle the position using the same strategy-switch / ownership-transition semantics used elsewhere
- treat upgrade as a source of strategy switch, not as a separate trading philosophy

## User terminology

- **strategy upgrade event** = the promotion-triggered online upgrade handling path
- **review** = upgrade validation / execution diagnosis sub-step
- **calibrate** = deprecated legacy reset/baseline-refresh term; not part of the default strategy-switch path

## Main code / script touchpoints

### Long-running runtime state
- `src/runners/trade_daemon.py`
- `src/runtime/mode.py`
- `src/runtime/mode_policy.py`
- `src/runtime/workflow.py`
- `src/runtime/workflows.py`

### Active strategy hot-swap / pointer
- `src/runtime/strategy_pointer.py`
- `src/runners/promote_strategy.py`
- `src/runners/process_strategy_upgrade_request.py`
- `src/runners/strategy_upgrade_event.py`

### Runtime state / execution coupling
- `src/execution/pipeline.py`
- `src/state/store.py`
- `src/state/live_position.py`

## Rule of thumb

Think of the system as:
- `trade` = the continuous state
- `strategy_upgrade_event` = the main upgrade-time event
- `review` = an internal event part, not a first-class mode
- `calibrate` = deprecated legacy term, not a first-class mode and not part of the default upgrade event path
