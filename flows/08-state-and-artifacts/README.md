# 08 State and Artifacts

This flow step covers persistent live state and the artifact/state boundary used by runtime and upgrade handling.

## Responsibility

- store live state
- represent open positions and ownership metadata
- expose runtime log/state helper paths
- support handover observation and upgrade-related state markers

## Current contents

- `src/state/store.py`
- `src/state/live_position.py`
- `src/state/models.py`
- `src/runtime/store.py`
- `src/runtime/log_paths.py`

## Likely next additions

- handover marker helpers if extracted
- any additional state serializers or runtime-state wrappers needed by upgrade processing

## Expected future home

These files will likely land in final `src/state/` and `src/runtime/` areas inside `quantitative-trading`.
