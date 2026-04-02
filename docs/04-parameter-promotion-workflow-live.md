# Parameter Promotion Workflow (Live Side)

This document keeps only the live-runtime side of parameter/strategy promotion.

## Boundary

Historical research is responsible for:
- deciding whether a new family / variant / parameter set should be promoted
- ranking / selection / retune / archive decisions

The live runtime is responsible for:
- consuming the promoted result
- detecting active strategy changes
- continuing execution with the new version
- validating upgrade-time execution behavior

Live runtime does **not** optimize the model directly.

## Goal

When historical research finds a better strategy/parameter version, the live runtime should be able to adopt it immediately and safely without stopping the trade daemon.

## Canonical live workflow

1. historical system produces a promoted strategy/parameter version
2. active strategy pointer is updated
3. trade daemon detects the active version change while continuing to run
4. daemon emits a `strategy_upgrade_event_requested` signal / request artifact
5. out-of-band consumer processes the unified `strategy_upgrade_event`
6. live runtime continues trading under the new active version

## Upgrade event meaning

`strategy_upgrade_event` is the unified promotion-time event.

It now centers on:
- position handover observation / decision / marker
- review / execution-diagnosis work

The old `calibrate` concept has been removed from the strategy-switch flow and is no longer part of the default promotion-time event path.

## Position handling rule

If an active strategy change happens while a position is open:
- do not require a special upgrade-only flatten
- reuse normal strategy-switch / ownership-transition handling
- record the handover policy, observation, decision, and marker

## Safety rules

- only whitelisted tunable keys may be overridden
- credentials, account aliases, and execution-mode flags must not be overridden by research candidates
- invalid active parameter file must fail closed to baseline defaults
- promotion must never silently modify API credentials or account routing

## Runtime-side outputs

The live side should be able to record:
- active strategy version metadata in execution artifacts
- hot-swap detection events
- strategy upgrade request/result artifacts
- position handover observation / decision / marker when an upgrade happens with open positions

## Main code / script touchpoints

### Active strategy publication / pointer handling
- `src/upgrade/strategy_pointer.py`
- `src/upgrade/promote_strategy.py`

### Upgrade detection / request
- `src/runtime/trade_daemon.py`
- `src/upgrade/process_strategy_upgrade_request.py`

### Unified upgrade event
- `src/runtime/workflows.py`
- `src/runtime/workflows.py`
- `src/runtime/workflows.py`


### Artifact tagging
- `src/execution/pipeline.py`
- `src/execution_cycle.py`
