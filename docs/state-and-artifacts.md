# State and Artifacts

## State responsibilities

Live state tracks things such as:
- open positions
- ownership / handover-related metadata when upgrades happen during open positions
- execution history pointers
- active strategy pointer metadata needed for live runtime decisions

## Runtime artifacts

Primary runtime artifacts include:
- `logs/runtime/latest-execution-cycle.json`
- `logs/runtime/execution-cycles/YYYY-MM-DD.jsonl`
- `logs/runtime/latest-strategy-upgrade-request.json`
- `logs/runtime/latest-strategy-upgrade-result.json`
- `logs/runtime/latest-strategy-handover-marker.json`

## Current state model

Artifacts and state are part of the traceable live review path, not just debugging leftovers.

## Main code / script touchpoints

- `src/state/store.py`
- `src/state/live_position.py`
- `src/runtime/strategy_pointer.py`
- `src/runners/process_strategy_upgrade_request.py`
- `src/runners/execution_cycle.py`
- `src/execution/pipeline.py`
