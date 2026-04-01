# State and Artifacts

## State path

State tracks things such as:
- open positions keyed as `strategy:symbol`
- last signal per strategy/symbol bucket
- per-bucket capital (`initial_capital_usdt`, `available_usdt`, `allocated_usdt`)
- execution history

## Runtime artifacts

Primary runtime artifacts:
- `logs/runtime/latest-execution-cycle.json`
- `logs/runtime/execution-cycles/YYYY-MM-DD.jsonl` (business-timezone daily partitions in `America/New_York`)

## Current state

Artifacts are part of the traceable review data path, not just debugging leftovers.
