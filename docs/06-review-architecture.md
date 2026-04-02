# Review Architecture

## Purpose

The review system turns runtime execution history into:
- upgrade-validation reports
- operator-readable execution diagnostics
- realized live-performance summaries for the currently promoted live strategy
- portable JSON/Markdown review artifacts

## Core architectural shift

Realtime review is no longer modeled as the place where strategy optimization happens.

Instead:
- model optimization happens on the historical/backtest line
- realtime review focuses on execution fidelity and operational health

This means review should center on:
- theoretical vs actual execution
- position drift
- execution errors and instability
- upgrade-impact validation

At the current migration stage, the review/export side now has a dedicated execution-deviation layer, but it only becomes informative on cycles that actually contain realized pnl / fee / funding observations. Hold-only dummy cycles may still render that section as placeholder.

## Primary trigger

The primary trigger for full review is now:
- strategy / parameter promotion
- active strategy version change
- `strategy_upgrade_event`

Scheduled weekly/monthly/quarterly summaries may still exist as secondary operational health reports, but they are no longer the core review identity.

## High-level pipeline

1. runtime writes execution artifacts under `logs/runtime/`
2. trade daemon detects active strategy version changes while continuing to run
3. daemon emits `strategy_upgrade_event_requested` and related request artifacts out-of-band
4. upgrade consumer runs the unified `strategy_upgrade_event`
5. review/export path summarizes execution quality and deviation around the upgrade context

## Runtime artifact reality

The review path should assume:
- a continuously running trade daemon
- a currently active promoted strategy/model version
- potential hot-swap between promoted versions without daemon restart
- no standing parallel live-account comparison matrix as the core operating model

### Core artifact families
- execution cycle artifacts
- strategy upgrade request/result artifacts
- handover markers for upgrade-time position handling

## Review emphasis

### Execution fidelity
Was the intended strategy behavior actually expressed in orders and positions?

### Position fidelity
Did actual positions stay aligned with intended positions and ownership?

### Upgrade validation
What changed after the active strategy version changed?
Did execution quality worsen, remain stable, or improve?

### Operational health
Were there rejects, state desyncs, stale signals, or reconciliation issues?

## Position handling during upgrade

When an upgrade occurs while a position is open:
- treat it as a strategy-switch / ownership-transition problem
- do not introduce a separate mandatory upgrade-time flatten rule
- record the handover observation, decision, and marker for auditability

## Output model

A full upgrade-oriented review should be able to describe:
- previous strategy version
- current active strategy version
- switch boundary / observed upgrade time
- pre/post-upgrade execution observations
- deviation summary
- handover decision / marker when relevant

## Main code / script touchpoints

### Artifact production
- `src/execution/pipeline.py`
- `src/execution_cycle.py`
- `src/upgrade/strategy_pointer.py`
- `src/upgrade/process_strategy_upgrade_request.py`

### Review transformation / export
- `src/review/ingestion.py`
- `src/review/aggregator.py`
- `src/review/performance.py`
- `src/review/report.py`
- `src/review/export.py`

### Upgrade event orchestration
- `src/upgrade/process_strategy_upgrade_request.py`
- `src/runtime/workflows.py`
