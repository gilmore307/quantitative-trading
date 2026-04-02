# Research / Runtime Separation (Live Side)

This document keeps only the runtime-side interpretation of research/runtime separation.

## Core split

There are two parallel lines:

### Historical research / backtest line
Responsible for:
- extending historical data
- adding new symbols
- adding new families / variants
- ranking / selection / retune / archive
- optimizing models and parameters

### Realtime trading line
Responsible for:
- consuming the currently promoted model
- trading with it continuously
- generating real execution history and review data
- validating execution fidelity and operational health

The realtime trading line consumes models.
It does not directly train or optimize them.

## Goal

Keep live runtime execution operationally independent from historical research while still letting the live side consume promoted outputs.

## Runtime path responsibilities

Entry:
- `src/runtime/trade_daemon.py`

Responsibilities:
- fetch current market/exchange state
- run execution pipeline
- reconcile local/exchange state
- place demo/live orders when allowed
- persist runtime artifacts
- keep reading the latest active strategy pointer
- continue through strategy upgrades without stopping the daemon
- emit out-of-band upgrade validation requests when active strategy changes

## Runtime must not do

The live runtime should not directly be the place where we:
- rank families
- re-score variants
- retune parameters
- decide promotion/demotion
- update the model based on ad-hoc live noise

Those belong to the historical line.

## Runtime review role

Live review should provide:
- deviation facts
- execution anomalies
- operational health observations
- clues for later research-side investigation

It should not directly mutate the model-selection logic.

## Rule

Artifact compatibility is allowed; operational dependence is not.

Research may consume runtime artifacts.
Runtime should not need research processes to stay alive.

## Main code / script touchpoints

### Live runtime line
- `src/runtime/trade_daemon.py`
- `src/execution/pipeline.py`
- `src/upgrade/strategy_pointer.py`
- `src/state/`
- `src/reconcile/`

### Upgrade-event / validation bridge
- `src/upgrade/process_strategy_upgrade_request.py`
- `src/runtime/workflows.py`
- `src/runtime/workflows.py`

### Live-side review outputs
- `src/review/`
- `src/runtime/workflows.py`
- `dashboard-side consumer (future)`
- `dashboard-side consumer (future)`
- `dashboard-side consumer (future)`
