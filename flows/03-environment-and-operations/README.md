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
#### entrypoints
- `scripts/entrypoints/execution_cycle.py`
- `scripts/entrypoints/regime_snapshot.py`

#### monitors
- `scripts/monitors/shock_snapshot.py`
- `scripts/monitors/trade_alert_scan.py`

## Notes on current cleanup

This flow step has already been cleaned to remove old `crypto-trading` working-directory paths from the migrated daemon/service wrappers.

## Likely future additions

- additional service/unit files used by the live runtime
- operation-specific helper scripts tied to runtime startup and service management
- migration of more runtime-side shell helpers if they remain part of the live system

## Expected future home

This step will likely collect operational scripts and service-facing helpers rather than core runtime logic.
