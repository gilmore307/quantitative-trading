# Multi-Account Parallel Execution

_Last updated: 2026-03-20_

## Goal

Run all strategy accounts in parallel:

- `trend`
- `crowded`
- `meanrev`
- `compression`
- `realtime`

The market-state / regime-detection layer may remain shared, but real execution should no longer be limited to one routed account per cycle.

## Current status

### Already landed
- `src.strategies.executors.build_parallel_plans(output)` exists
- `ExecutionPipeline.build_parallel_plans(output)` exists
- `ExecutionPipeline.run_cycle_parallel()` exists
- daemon has started moving onto the parallel-cycle path
- parallel execution artifacts are now being written

## Architectural rule

Going forward:
- shared market-state detection is allowed
- shared single-account routing as the only real execution path is not
- every strategy account must be able to trade in the same cycle if its own executor conditions are met
