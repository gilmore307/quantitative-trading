# 09 Execution Artifacts

This flow step covers live execution-cycle production and artifact persistence.

## Responsibility

- run the live execution pipeline
- generate execution-cycle results
- persist execution artifacts and related summary metadata
- carry active-strategy metadata into the artifact layer

## Current contents

### pipeline
- `pipeline/pipeline.py`
- `pipeline/controller.py`

### policy
- `policy/policy.py`

### verification
- `verification/confirm.py`

### exchange
- `exchange/exchange_snapshot.py`
- `exchange/adapters.py`

### plumbing
- `plumbing/identifiers.py`
- `plumbing/locks.py`

### runners
- `runners/execution_cycle.py`

## Notes on current cleanup

This flow step is now grouped by execution responsibility rather than by the old flat `src/execution/` copy layout.

## Likely next additions

- artifact schema helpers if they get separated later
- any remaining execution-adjacent helpers that are still outside this flow step

## Expected future home

These files will likely consolidate into the final `src/execution/` tree plus selected `src/runners/` entrypoints in `quantitative-trading`.
