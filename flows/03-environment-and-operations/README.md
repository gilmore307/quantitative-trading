# 03 Environment and Operations

This flow step covers how the live runtime is started, operated, and kept safe.

## Responsibility

- document runtime startup paths
- describe environment/runtime configuration expectations
- anchor live-operational safety practices
- keep daemon operations separate from model-optimization concerns

## Current contents

### Startup / service entrypoints
- `run_daemon.sh`
- `systemd/quantitative-trading.service`

### Runtime helper scripts
- `scripts/runtime/execution_cycle.py`
- `scripts/runtime/regime_snapshot.py`
- `scripts/runtime/shock_snapshot.py`
- `scripts/runtime/trade_alert_scan.py`

## Likely future additions

- any additional service/unit files used by the live runtime
- operation-specific helper scripts tied to runtime startup and service management
- migration of more runtime-side shell helpers if they remain part of the live system

## Expected future home

This step will likely collect operational scripts and service-facing helpers rather than core runtime logic.
