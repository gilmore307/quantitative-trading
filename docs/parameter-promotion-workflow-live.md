# Parameter Promotion Workflow (Live Side)

This document keeps only the live-runtime side of parameter promotion.

## Goal

When historical research finds a better parameter set, the live runtime should be able to adopt it immediately and safely.

## Live-side responsibilities

- load promoted active parameter versions
- keep activation / rollback explicit
- never let research candidates directly mutate live credentials or routing
- attach active parameter version metadata to live runtime artifacts and review outputs

## Current live workflow

1. historical system produces a promotion candidate elsewhere
2. live system receives an activation decision
3. active parameter storage is updated
4. daemon picks up the active parameter version
5. rollback remains explicit and auditable

## Safety rules

- only whitelisted tunable keys may be overridden
- credentials, account aliases, and execution-mode flags must not be overridden by research candidates
- invalid active parameter file must fail closed to baseline defaults
- promotion must never silently modify API credentials or account routing
