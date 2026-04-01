# 02 Runtime and Modes

This flow step covers the always-on live runtime state.

## Responsibility

- define the long-running runtime state model
- keep `trade` as the continuous daemon state
- treat review/calibrate as event concepts rather than standalone runtime modes
- provide the runtime workflow/event semantics that the daemon uses

## Current contents

- `src/runners/trade_daemon.py`
- `src/runtime/mode.py`
- `src/runtime/mode_policy.py`
- `src/runtime/workflow.py`
- `src/runtime/workflows.py`

## Likely next additions

- any remaining runtime-mode policy helpers
- daemon-adjacent runtime orchestration helpers still left outside this flow step

## Expected future home

These files will likely end up under the final `src/runtime/` and `src/runners/` layout of `quantitative-trading`.
