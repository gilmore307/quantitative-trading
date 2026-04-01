# Regime and Decision Flow

This document describes the current decision path for the live execution system.

## Purpose

The system is designed around this rule:

- interpret current market state first
- decide whether the active promoted trading instructions permit action
- execute and reconcile

The intent is to avoid treating execution logic itself as the place where model optimization happens.

## Main entrypoints

### Trade daemon
- `src/runners/trade_daemon.py`

### Execution pipeline
- `src/execution/pipeline.py`

Produces:
- `ExecutionCycleResult`
- `ExecutionDecisionTrace`

## Current interpretation

The current live model assumes:
- one live account
- one active promoted strategy / instruction set at a time
- a continuously running trade daemon
- strategy upgrades handled as promotion-triggered events rather than mode switches

## Decision flow

Current high-level flow is:

1. current market/exchange state is fetched
2. active strategy / instruction pointer is read
3. execution pipeline checks whether action is permitted under current runtime state and active inputs
4. execution plan is produced or blocked
5. execution / verification / reconcile artifacts are persisted

## Runtime mode interaction

Runtime mode is still relevant because it affects whether normal execution is allowed.

Examples:
- `develop` may block normal trade execution
- `trade` permits normal live execution
- `test` and `reset` are exceptional operational states

## Main code / script touchpoints

- `src/runners/trade_daemon.py`
- `src/execution/pipeline.py`
- `src/runtime/mode.py`
- `src/runtime/mode_policy.py`
- `src/runtime/strategy_pointer.py`
- `src/state/store.py`
- `src/reconcile/`
