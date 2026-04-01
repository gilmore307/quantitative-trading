# 02 Runtime and Modes

This flow step covers the always-on live runtime state.

## Responsibility

- define the long-running runtime state model
- keep `trade` as the continuous daemon state
- treat review/calibrate as event concepts rather than standalone runtime modes
- provide the runtime workflow/event semantics that the daemon uses

## Current contents

### daemon
- `daemon/trade_daemon.py`

### mode
- `mode/mode.py`
- `mode/mode_policy.py`

### workflows
- `workflows/workflow.py`
- `workflows/workflows.py`

## Expected future home

These files will likely end up under the final `src/runtime/` and `src/runners/` layout of `quantitative-trading`.
