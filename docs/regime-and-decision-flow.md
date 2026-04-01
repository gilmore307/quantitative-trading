# Regime and Decision Flow

This document backfills the meta-work for the regime pipeline and execution decision path.

## Purpose

The system is designed around this rule:

- classify regime first
- route second
- execute third

The intent is to avoid treating execution logic as the place where market understanding happens.

## Main entrypoints

### Regime runner
- `src/runners/regime_runner.py`

### Execution pipeline
- `src/execution/pipeline.py`

Produces:
- `ExecutionCycleResult`
- `ExecutionDecisionTrace`

## Runtime mode interaction

Runtime mode is not just a label. It changes whether normal routing is allowed.

Examples:
- `develop` may block normal routing workflows
- `trade` permits normal routing
- `test` and `reset` are exceptional operational states with different policy implications from normal trading
