# 07 Regime and Decision Flow

This flow step covers the decision path between current market interpretation, active promoted inputs, and execution permission.

## Responsibility

- describe how the daemon reaches an execution decision
- hold regime/declaration entrypoints that still belong to the live path
- keep execution-policy helpers close to the decision narrative

## Current contents

### regime
- `regime/regime_runner.py`

### decision
- `decision/policy.py`
- `decision/confirm.py`

## Expected future home

These files will likely split between final `src/runners/`, `src/execution/`, and possibly a smaller live-decision package inside `quantitative-trading`.
