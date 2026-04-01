# Multi-Account Parallel Execution

## Status

This document is now retained only as **legacy / transitional context** from the older hybrid repository.

It does **not** describe the current primary operating model for `quantitative-trading`.

## Current primary operating model

The current live trading model is:
- one live account
- one active promoted strategy / instruction set at a time
- continuous trade daemon
- upgrade validation handled via `strategy_upgrade_event`

## Why keep this document for now

Some old code, field names, and review/export structures may still reference parallel-account or router/composite ideas from the earlier design.

This document is kept temporarily so those references can be recognized and migrated cleanly.

## Migration rule

Do not treat this document as the target architecture.

When code or scripts are migrated into `quantitative-trading`, prefer the single-account live model unless a later deliberate design change says otherwise.

## Likely legacy-touch modules

- `src/execution/pipeline.py`
- `src/runners/execution_cycle.py`
- `src/review/`
- `src/routing/`
- `src/strategies/executors.py`
