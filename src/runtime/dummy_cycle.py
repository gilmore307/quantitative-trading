from __future__ import annotations

import json
from dataclasses import asdict
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

from src.execution.adapters import DryRunExecutionAdapter, ExecutionReceipt
from src.execution.pipeline import ExecutionCycleResult, ExecutionDecisionTrace, ActiveStrategyExecutionResult
from src.runtime.regime_runner import RegimeRunnerOutput
from src.runtime.store import RuntimeStore
from src.state.live_position import LivePosition, LivePositionStatus
from src.execution.plan import ExecutionPlan
from src.upgrade.strategy_pointer import ActiveStrategySnapshot


STATE_PATH = Path('/root/.openclaw/workspace/projects/quantitative-trading/logs/runtime/dummy-cycle-state.json')
DUMMY_ACCOUNT_ALIAS = 'active_live'
DUMMY_SYMBOL = 'BTC-USDT-SWAP'


def _load_state() -> dict[str, Any]:
    if not STATE_PATH.exists():
        return {}
    try:
        return json.loads(STATE_PATH.read_text(encoding='utf-8'))
    except Exception:
        return {}


def _save_state(payload: dict[str, Any]) -> None:
    STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
    STATE_PATH.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding='utf-8')


def _interval_seconds_for_version(version: str) -> float:
    version = str(version or '').lower()
    if 'v2' in version or 'dummy-2' in version or 'upgrade' in version or '3s' in version:
        return 3.0
    return 5.0


def _build_regime_output(active: ActiveStrategySnapshot) -> RegimeRunnerOutput:
    now = datetime.now(UTC)
    family = str((active.metadata or {}).get('family') or 'dummy')
    decision_summary = {
        'regime': family,
        'confidence': 1.0,
        'tradable': True,
        'account': DUMMY_ACCOUNT_ALIAS,
        'active_route': 'active_live',
        'trade_enabled': True,
        'allow_reason': 'dummy_live_cycle_enabled',
        'block_reason': None,
        'reasons': ['dummy_live_cycle_enabled'],
        'secondary': [],
        'diagnostics': ['dummy_live_cycle_enabled'],
    }
    return RegimeRunnerOutput(
        observed_at=now,
        symbol=DUMMY_SYMBOL,
        background_4h={'primary': family, 'confidence': 1.0, 'reasons': ['dummy_live_cycle'], 'secondary': [], 'tradable': True, 'scores': {family: 1.0}},
        primary_15m={'primary': family, 'confidence': 1.0, 'reasons': ['dummy_live_cycle'], 'secondary': [], 'tradable': True, 'scores': {family: 1.0}},
        override_1m={'primary': family, 'confidence': 1.0, 'reasons': ['dummy_live_cycle'], 'secondary': [], 'tradable': True, 'scores': {family: 1.0}},
        background_features={'adx': 30.0, 'last_price': 100000.0, 'ema20_slope': 1.0, 'ema50_slope': 1.0},
        primary_features={'adx': 25.0, 'last_price': 100000.0, 'vwap_deviation_z': 0.5, 'bollinger_bandwidth_pct': 0.02, 'realized_vol_pct': 0.5, 'funding_pctile': 0.5, 'oi_accel': 0.1, 'basis_deviation_pct': 0.001},
        override_features={'last_price': 100000.0, 'vwap_deviation_z': 0.4, 'trade_burst_score': 0.7, 'liquidation_spike_score': 0.0, 'orderbook_imbalance': 0.0, 'realized_vol_pct': 0.5},
        final_decision={'primary': family, 'confidence': 1.0, 'reasons': ['dummy_live_cycle'], 'secondary': [], 'tradable': True},
        route_decision={'regime': family, 'account': DUMMY_ACCOUNT_ALIAS, 'active_route': 'active_live', 'trade_enabled': True, 'allow_reason': 'dummy_live_cycle_enabled', 'block_reason': None},
        decision_summary=decision_summary,
        settings=None,
    )


def _build_receipt(action: str, side: str | None, size: float | None, interval_seconds: float, active: ActiveStrategySnapshot) -> ExecutionReceipt:
    adapter = DryRunExecutionAdapter()
    if action == 'enter' and side is not None and size is not None:
        receipt = adapter.submit_entry(account=DUMMY_ACCOUNT_ALIAS, symbol=DUMMY_SYMBOL, side=side, size=size, reason=f'dummy_enter_{interval_seconds}s')
    elif action == 'exit':
        receipt = adapter.submit_exit(account=DUMMY_ACCOUNT_ALIAS, symbol=DUMMY_SYMBOL, reason=f'dummy_exit_{interval_seconds}s', requested_size=size)
    else:
        raise ValueError(f'unsupported dummy receipt action: {action}')
    raw = dict(receipt.raw or {})
    raw.update({
        'account_alias': DUMMY_ACCOUNT_ALIAS,
        'account_label': 'Active Live Dummy',
        'dummy_cycle': True,
        'dummy_strategy_version': active.version,
        'fee_usdt': 0.12 if action == 'enter' else 0.08,
        'funding_usdt': 0.01 if action == 'exit' else 0.0,
        'realized_pnl_usdt': 0.45 if action == 'exit' else 0.0,
        'unrealized_pnl_usdt': 0.0,
        'pnl_usdt': 0.45 if action == 'exit' else 0.0,
        'equity_usdt': 10000.45 if action == 'exit' else 10000.0,
        'equity_end_usdt': 10000.45 if action == 'exit' else 10000.0,
        'fill_count': 1,
        'trade_ids': receipt.trade_ids or [f'dummy-{action}-{int(datetime.now(UTC).timestamp())}'],
    })
    receipt.raw = raw
    return receipt


def run_dummy_cycle(*, runtime_store: RuntimeStore, active: ActiveStrategySnapshot) -> ActiveStrategyExecutionResult:
    now = datetime.now(UTC)
    state = _load_state()
    current_version = str(active.version or 'dummy-v1')
    previous_version = str(state.get('active_version') or '')
    if previous_version != current_version:
        state = {'active_version': current_version}
    interval_seconds = _interval_seconds_for_version(current_version)
    last_entered_at = datetime.fromisoformat(state['last_entered_at']) if state.get('last_entered_at') else None
    last_exited_at = datetime.fromisoformat(state['last_exited_at']) if state.get('last_exited_at') else None
    position_open = bool(state.get('position_open', False))

    action = 'hold'
    side = 'long'
    size = 1.0
    if not position_open and (last_exited_at is None or now - last_exited_at >= timedelta(seconds=interval_seconds)):
        action = 'enter'
    elif position_open and (last_entered_at is None or now - last_entered_at >= timedelta(seconds=interval_seconds)):
        action = 'exit'

    plan = ExecutionPlan(
        regime=str((active.metadata or {}).get('family') or 'dummy'),
        account=DUMMY_ACCOUNT_ALIAS,
        action=action,
        side=side if action == 'enter' else None,
        size=size if action in {'enter', 'exit'} else None,
        reason=f'dummy_cycle_{int(interval_seconds)}s',
        score=1.0,
        blockers=[],
        signals={'dummy_interval_seconds': interval_seconds, 'position_open': position_open},
        subscores={'dummy_live_cycle': 1.0},
    )
    trace = ExecutionDecisionTrace(
        mode=runtime_store.get().mode.value,
        mode_allows_routing=True,
        decision_trade_enabled=True,
        route_trade_enabled=True,
        pipeline_trade_enabled=True,
        pipeline_entered=True,
        submission_allowed=action in {'enter', 'exit'},
        submission_attempted=action in {'enter', 'exit'},
        allow_reason='dummy_live_cycle_enabled',
        block_reason=None,
        diagnostics=['dummy_live_cycle_enabled'],
    )

    receipt = None
    local_position = None
    if action in {'enter', 'exit'}:
        receipt = _build_receipt(action, side if action == 'enter' else None, size, interval_seconds, active)
    if action == 'enter':
        state['position_open'] = True
        state['last_entered_at'] = now.isoformat()
        local_position = LivePosition(
            account=DUMMY_ACCOUNT_ALIAS,
            symbol=DUMMY_SYMBOL,
            route=plan.regime,
            status=LivePositionStatus.OPEN,
            side=side,
            size=size,
            entry_order_id=receipt.order_id if receipt else None,
            entry_execution_id=receipt.execution_id if receipt else None,
            entry_client_order_id=receipt.client_order_id if receipt else None,
            entry_trade_ids=receipt.trade_ids if receipt else None,
            reason=plan.reason,
            meta={'dummy_interval_seconds': interval_seconds, 'dummy_strategy_version': active.version},
        )
    elif action == 'exit':
        state['position_open'] = False
        state['last_exited_at'] = now.isoformat()
        local_position = LivePosition(
            account=DUMMY_ACCOUNT_ALIAS,
            symbol=DUMMY_SYMBOL,
            route=plan.regime,
            status=LivePositionStatus.FLAT,
            side=None,
            size=0.0,
            exit_order_id=receipt.order_id if receipt else None,
            exit_execution_id=receipt.execution_id if receipt else None,
            exit_client_order_id=receipt.client_order_id if receipt else None,
            exit_trade_ids=receipt.trade_ids if receipt else None,
            reason=plan.reason,
            meta={'dummy_interval_seconds': interval_seconds, 'dummy_strategy_version': active.version},
        )
    else:
        local_position = LivePosition(
            account=DUMMY_ACCOUNT_ALIAS,
            symbol=DUMMY_SYMBOL,
            route=plan.regime,
            status=LivePositionStatus.OPEN if position_open else LivePositionStatus.FLAT,
            side='long' if position_open else None,
            size=1.0 if position_open else 0.0,
            reason=plan.reason,
            meta={'dummy_interval_seconds': interval_seconds, 'dummy_strategy_version': active.version},
        )

    _save_state(state)
    regime_output = _build_regime_output(active)
    cycle = ExecutionCycleResult(
        regime_output=regime_output,
        plan=plan,
        receipt=receipt,
        local_position=local_position,
        verification_position=local_position,
        reconcile_result=None,
        decision_trace=trace,
        runtime_state=asdict(runtime_store.get()),
        active_strategy=asdict(active),
        route_state={'enabled': True, 'frozen_reason': None},
        live_positions=[asdict(local_position)],
    )
    return ActiveStrategyExecutionResult(
        regime_output=regime_output,
        strategy_name=str((active.metadata or {}).get('family') or 'dummy'),
        result=cycle,
        runtime_state=asdict(runtime_store.get()),
        active_strategy=asdict(active),
        live_positions=[asdict(local_position)],
    )
