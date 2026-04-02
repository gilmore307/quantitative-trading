# Runtime and Modes

## Goal

Document the long-running runtime state model and the event model around strategy upgrades.

## Long-running modes

Only long-lived runtime states should be modeled as modes:

- `develop` — idle development / maintenance mode; do not run normal strategy execution or routing
- `trade` — normal trading mode; the long-running daemon state that executes the current active strategy
- `reset` — development-only destructive reset/testing helper path; not part of the default strategy-upgrade flow
- `test` — dedicated execution-system test mode; does not run normal strategy logic and should return to `develop`

## Events / jobs

These are not long-running modes.
They are events/jobs that happen around the always-on trade daemon.

- `strategy_upgrade_event` — the canonical promotion-triggered upgrade event
- `review` — upgrade validation / execution diagnosis sub-step
- `calibrate` — removed legacy label; not part of the default strategy-upgrade flow anymore

## Core runtime interpretation

### Trade daemon

`trade` is the only normal always-on live-trading state.

The daemon should:
- keep running continuously
- keep reading the current active strategy pointer
- detect active strategy version changes without requiring a restart
- continue trading with the new active strategy version once detected
- emit upgrade-related request artifacts out-of-band instead of blocking the main loop

### Review is not a mode

`review` should no longer be treated as a standalone runtime mode.

It is best understood as:
- a helper/event concept
- a sub-step of the broader `strategy_upgrade_event`

The old `calibrate` concept has been removed from the default strategy-switch flow because strategy performance is measured from segment-start account state to segment-end account state rather than by forcing a reset baseline.

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
- **calibrate** = removed legacy reset/baseline-refresh term; not part of the strategy-switch path

## Main code / script touchpoints

### Long-running runtime state
- `src/runners/trade_daemon.py`
- `src/runtime/mode.py`
- `src/runtime/mode_policy.py`
- `src/runtime/workflow.py`
- `src/runtime/workflows.py`

### Active strategy hot-swap / pointer
- `src/upgrade/strategy_pointer.py`
- `src/runners/promote_strategy.py`
- `src/upgrade/process_strategy_upgrade_request.py`
- `src/runtime/workflows.py`

### Runtime state / execution coupling
- `src/execution/pipeline.py`
- `src/state/store.py`
- `src/state/live_position.py`

## Rule of thumb

Think of the system as:
- `trade` = the continuous state
- `strategy_upgrade_event` = the main upgrade-time event
- `review` = an internal event part, not a first-class mode
- `calibrate` = removed legacy term, not a first-class mode and not part of the upgrade event path
