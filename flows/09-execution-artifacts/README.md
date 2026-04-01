# 09 Execution Artifacts

This flow step covers live execution-cycle production and artifact persistence.

## Responsibility

- run the live execution pipeline
- generate execution-cycle results
- persist execution artifacts and related summary metadata
- carry active-strategy metadata into the artifact layer

## Current contents

- `src/runners/execution_cycle.py`
- `src/execution/`

## Likely next additions

- any remaining execution-adjacent helpers still sitting outside `src/execution/`
- artifact schema helpers if they get separated later

## Expected future home

These files will likely stay close to final `src/execution/` plus selected `src/runners/` entrypoints in `quantitative-trading`.
