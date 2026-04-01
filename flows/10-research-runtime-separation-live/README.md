# 10 Research / Runtime Separation (Live Side)

This flow step collects the live-only runtime pieces that must stay operationally independent from historical research.

## Responsibility

- keep the live runtime autonomous
- keep notifier / watcher / loop helpers on the runtime side
- make it clear which runtime helpers belong to the live system rather than the historical modeling system

## Current contents

- `src/runners/realtime_engine.py`
- `src/runners/minute_engine.py`
- `src/runners/shock_monitor.py`
- `src/runners/trade_alert_watcher.py`
- `src/runners/discord_notifier.py`
- `src/runtime/business_time.py`
- `src/runtime/bucket_state.py`

## Likely next additions

- any remaining live-only loop helpers
- notifier / alert support code still outside this flow step
- runtime-only scheduling helpers

## Expected future home

These files will likely land across final `src/runners/`, `src/runtime/`, and notification/ops helper areas inside `quantitative-trading`.
