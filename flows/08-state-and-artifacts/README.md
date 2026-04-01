# 08 State and Artifacts

This flow step covers persistent live state and the artifact/state boundary used by runtime and upgrade handling.

## Responsibility

- store live state
- represent open positions and ownership metadata
- expose runtime log/state helper paths
- support handover observation and upgrade-related state markers

## Current contents

### live-state
- `live-state/store.py`

### position
- `position/live_position.py`

### models
- `models/models.py`

### runtime-state
- `runtime-state/store.py`
- `runtime-state/log_paths.py`

## Likely next additions

- handover marker helpers if extracted
- additional state serializers used by upgrade processing
- pointer/state bridge helpers if they separate from the main runtime modules

## Expected future home

These files will likely land in final `src/state/` and `src/runtime/` areas inside `quantitative-trading`.
