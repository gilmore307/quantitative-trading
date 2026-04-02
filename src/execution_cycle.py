from __future__ import annotations

import json
from dataclasses import asdict
from datetime import UTC, datetime
from typing import Any

from src.execution.pipeline import ExecutionCycleResult, ExecutionPipeline, ActiveStrategyExecutionResult
from src.review.account_metrics import build_account_metrics_from_cycle
from src.state.log_paths import RUNTIME_DIR, dated_jsonl_path


OUT_DIR = RUNTIME_DIR
LATEST_PATH = OUT_DIR / 'latest-execution-cycle.json'
HISTORY_PATH = lambda: dated_jsonl_path('execution-cycles')
DETAILED_HISTORY_PATH = lambda: dated_jsonl_path('execution-cycle-details')
ANOMALY_HISTORY_PATH = lambda: dated_jsonl_path('execution-anomalies')
REGIME_HISTORY_PATH = lambda: dated_jsonl_path('regime-local-history')
REDACT_KEYS = {
    'okx_api_key', 'okx_api_secret', 'okx_api_passphrase',
    'discord_bot_token', 'discord_webhook_url',
    'api_key', 'api_secret', 'api_passphrase', 'token', 'secret', 'passphrase', 'webhook_url',
}


def _resolve_path(path_or_factory):
    return path_or_factory() if callable(path_or_factory) else path_or_factory


def _json_default(value: Any):
    if isinstance(value, datetime):
        return value.astimezone(UTC).isoformat()
    return str(value)


def _append_jsonl(path_or_factory, payload: dict[str, Any]) -> None:
    with _resolve_path(path_or_factory).open('a', encoding='utf-8') as handle:
        handle.write(json.dumps(payload, default=_json_default, ensure_ascii=False) + '\n')


def _redact_value(value: Any) -> Any:
    if value is None:
        return None
    if isinstance(value, (bool, int, float)):
        return value
    text = str(value)
    if not text:
        return text
    return '***REDACTED***'


def _sanitize_for_artifact(value: Any) -> Any:
    if isinstance(value, dict):
        sanitized = {}
        for key, inner in value.items():
            if str(key).lower() in REDACT_KEYS:
                sanitized[key] = _redact_value(inner)
            else:
                sanitized[key] = _sanitize_for_artifact(inner)
        return sanitized
    if isinstance(value, list):
        return [_sanitize_for_artifact(item) for item in value]
    if hasattr(value, 'model_dump'):
        return _sanitize_for_artifact(value.model_dump())
    return value


def _sanitize_execution_payload(payload: dict[str, Any]) -> dict[str, Any]:
    cleaned = _sanitize_for_artifact(payload)
    regime_output = cleaned.get('regime_output')
    if isinstance(regime_output, dict) and 'settings' in regime_output:
        regime_output['settings'] = '[REDACTED_SETTINGS]'
    return cleaned


def _balance_summary_for_result(result: ExecutionCycleResult) -> dict[str, Any] | None:
    receipt = result.receipt
    if receipt is None or not receipt.accepted or not receipt.account:
        return None
    if receipt.mode not in {'okx_demo', 'okx_live'}:
        return None
    raw = receipt.raw if isinstance(receipt.raw, dict) else {}
    summary = {
        'account_alias': raw.get('account_alias') or receipt.account,
        'account_label': raw.get('account_label'),
        'equity_usdt': raw.get('equity_end_usdt', raw.get('equity_usdt')),
        'equity_end_usdt': raw.get('equity_end_usdt', raw.get('equity_usdt')),
        'realized_pnl_usdt': raw.get('realized_pnl_usdt'),
        'unrealized_pnl_usdt': raw.get('unrealized_pnl_usdt', raw.get('pnl_usdt')),
        'pnl_usdt': raw.get('pnl_usdt'),
    }
    if summary['equity_usdt'] is not None or summary['realized_pnl_usdt'] is not None or summary['unrealized_pnl_usdt'] is not None or summary['pnl_usdt'] is not None:
        return summary
    return None


def _strategy_stats_summary(result: ExecutionCycleResult) -> dict[str, Any]:
    meta = ((result.local_position.meta if result.local_position is not None else None) or {})
    if str(meta.get('strategy_stats_eligible') or '').lower() == 'false':
        return {
            'strategy_stats_eligible': False,
            'strategy_stats_reason': meta.get('strategy_stats_reason') or 'execution_recovery',
        }
    if result.receipt is None or not result.receipt.accepted:
        return {
            'strategy_stats_eligible': False,
            'strategy_stats_reason': 'receipt_not_accepted',
        }
    if result.reconcile_result is not None and not result.reconcile_result.alignment.ok:
        return {
            'strategy_stats_eligible': False,
            'strategy_stats_reason': result.reconcile_result.policy.reason,
        }
    return {
        'strategy_stats_eligible': True,
        'strategy_stats_reason': 'clean_execution',
    }


def _feature_snapshot(result: ExecutionCycleResult) -> dict[str, Any]:
    return {
        'background_4h': {
            'regime': result.regime_output.background_4h.get('primary'),
            'confidence': result.regime_output.background_4h.get('confidence'),
            'scores': result.regime_output.background_4h.get('scores'),
            'tradable': result.regime_output.background_4h.get('tradable'),
            'adx': result.regime_output.background_features.get('adx'),
            'last_price': result.regime_output.background_features.get('last_price'),
            'ema20_slope': result.regime_output.background_features.get('ema20_slope'),
            'ema50_slope': result.regime_output.background_features.get('ema50_slope'),
        },
        'primary_15m': {
            'regime': result.regime_output.primary_15m.get('primary'),
            'confidence': result.regime_output.primary_15m.get('confidence'),
            'scores': result.regime_output.primary_15m.get('scores'),
            'tradable': result.regime_output.primary_15m.get('tradable'),
            'adx': result.regime_output.primary_features.get('adx'),
            'last_price': result.regime_output.primary_features.get('last_price'),
            'vwap_deviation_z': result.regime_output.primary_features.get('vwap_deviation_z'),
            'bollinger_bandwidth_pct': result.regime_output.primary_features.get('bollinger_bandwidth_pct'),
            'realized_vol_pct': result.regime_output.primary_features.get('realized_vol_pct'),
            'funding_pctile': result.regime_output.primary_features.get('funding_pctile'),
            'oi_accel': result.regime_output.primary_features.get('oi_accel'),
            'basis_deviation_pct': result.regime_output.primary_features.get('basis_deviation_pct'),
        },
        'override_1m': {
            'regime': None if result.regime_output.override_1m is None else result.regime_output.override_1m.get('primary'),
            'confidence': None if result.regime_output.override_1m is None else result.regime_output.override_1m.get('confidence'),
            'scores': None if result.regime_output.override_1m is None else result.regime_output.override_1m.get('scores'),
            'tradable': None if result.regime_output.override_1m is None else result.regime_output.override_1m.get('tradable'),
            'last_price': result.regime_output.override_features.get('last_price'),
            'vwap_deviation_z': result.regime_output.override_features.get('vwap_deviation_z'),
            'trade_burst_score': result.regime_output.override_features.get('trade_burst_score'),
            'liquidation_spike_score': result.regime_output.override_features.get('liquidation_spike_score'),
            'orderbook_imbalance': result.regime_output.override_features.get('orderbook_imbalance'),
            'realized_vol_pct': result.regime_output.override_features.get('realized_vol_pct'),
        },
    }


def _theoretical_snapshot(result: ExecutionCycleResult) -> dict[str, Any]:
    plan = result.plan
    summary = result.regime_output.decision_summary or {}
    receipt_raw = result.receipt.raw if result.receipt is not None and isinstance(result.receipt.raw, dict) else {}
    fee_usdt = receipt_raw.get('fee_usdt')
    funding_usdt = receipt_raw.get('funding_usdt')
    realized_pnl_usdt = receipt_raw.get('realized_pnl_usdt')
    expected_notional_usdt = None
    settings = getattr(result.regime_output, 'settings', None)
    if plan.action == 'enter' and plan.size is not None and settings is not None:
        expected_notional_usdt = float(plan.size or 0.0) * float(getattr(settings, 'default_order_size_usdt', 0.0) or 0.0)
    confidence = result.regime_output.final_decision.get('confidence')
    theoretical_strength = float(plan.score) if plan.score is not None else (float(confidence) if confidence is not None else None)
    theoretical_gross_pnl_proxy_usdt = None
    if realized_pnl_usdt is not None or fee_usdt is not None or funding_usdt is not None:
        theoretical_gross_pnl_proxy_usdt = float(realized_pnl_usdt or 0.0) + float(fee_usdt or 0.0) + float(funding_usdt or 0.0)
    execution_drag_proxy_usdt = None if theoretical_gross_pnl_proxy_usdt is None and realized_pnl_usdt is None else float(theoretical_gross_pnl_proxy_usdt or 0.0) - float(realized_pnl_usdt or 0.0)
    return {
        'regime': plan.regime,
        'action': plan.action,
        'side': plan.side,
        'size': plan.size,
        'reason': plan.reason,
        'score': plan.score,
        'subscores': plan.subscores,
        'signals': plan.signals,
        'blockers': plan.blockers,
        'decision_confidence': confidence,
        'decision_trade_enabled': summary.get('trade_enabled'),
        'expected_notional_usdt': expected_notional_usdt,
        'theoretical_strength': theoretical_strength,
        'theoretical_gross_pnl_proxy_usdt': theoretical_gross_pnl_proxy_usdt,
        'realized_pnl_usdt': realized_pnl_usdt,
        'fee_usdt': fee_usdt,
        'funding_usdt': funding_usdt,
        'execution_drag_proxy_usdt': execution_drag_proxy_usdt,
    }


def _verification_snapshot(result: ExecutionCycleResult) -> dict[str, Any]:
    local = result.local_position
    meta = ((local.meta if local is not None else None) or {})
    hint = meta.get('last_verification_hint') if isinstance(meta.get('last_verification_hint'), dict) else {}
    attempts = hint.get('verification_attempts') or []
    trade_confirmed_attempts = [row for row in attempts if isinstance(row, dict) and bool(row.get('trade_confirmed'))]
    return {
        'entry_verified_hint': bool(hint.get('verified_entry')),
        'entry_trade_confirmed': bool(trade_confirmed_attempts),
        'entry_verification_attempt_count': len(attempts),
        'entry_trade_confirmed_attempt_count': len(trade_confirmed_attempts),
        'entry_verification_attempts': attempts,
        'local_position_reason': None if local is None else local.reason,
        'local_position_status': None if local is None else local.status.value,
    }


def _build_ledger_snapshot(result: ExecutionCycleResult) -> dict[str, Any] | None:
    local = result.local_position
    if local is None:
        return None
    return {
        'open_leg_count': len(local.open_legs),
        'closed_leg_count': len(local.closed_legs),
        'pending_exit_leg_count': 0 if local.pending_exit is None else len(local.pending_exit.allocations),
        'open_leg_ids': [leg.leg_id for leg in local.open_legs],
        'closed_leg_ids': [leg.leg_id for leg in local.closed_legs],
        'pending_exit_leg_ids': [] if local.pending_exit is None else [alloc.leg_id for alloc in local.pending_exit.allocations],
    }


def _build_attribution_snapshot(result: ExecutionCycleResult) -> dict[str, Any]:
    receipt = result.receipt
    local = result.local_position
    raw = {} if receipt is None or not isinstance(receipt.raw, dict) else receipt.raw
    return {
        'account': None if receipt is None else receipt.account,
        'execution_id': None if receipt is None else receipt.execution_id,
        'client_order_id': None if receipt is None else receipt.client_order_id,
        'order_id': None if receipt is None else receipt.order_id,
        'trade_ids': None if receipt is None else receipt.trade_ids,
        'trade_count': 0 if receipt is None or receipt.trade_ids is None else len(receipt.trade_ids),
        'fee_source': 'fill_aggregation' if raw.get('fill_count') else ('order_payload' if raw.get('fee_usdt') is not None else None),
        'realized_pnl_source': 'fill_aggregation' if raw.get('fill_count') else ('order_payload' if raw.get('realized_pnl_usdt') is not None else None),
        'equity_source': 'balance_summary' if raw.get('equity_end_usdt') is not None or raw.get('equity_usdt') is not None else None,
        'ledger': None if local is None else {
            'open_leg_ids': [leg.leg_id for leg in local.open_legs],
            'closed_leg_ids': [leg.leg_id for leg in local.closed_legs],
            'pending_exit_leg_ids': [] if local.pending_exit is None else [alloc.leg_id for alloc in local.pending_exit.allocations],
        },
    }


def build_execution_artifact(result: ExecutionCycleResult) -> dict[str, Any]:
    payload = _sanitize_execution_payload(asdict(result))
    payload['artifact_type'] = 'execution_cycle'
    payload['recorded_at'] = datetime.now(UTC).isoformat()
    payload['feature_snapshot'] = _feature_snapshot(result)
    payload['theoretical_snapshot'] = _theoretical_snapshot(result)
    payload['verification_snapshot'] = _verification_snapshot(result)
    payload['attribution_snapshot'] = _build_attribution_snapshot(result)
    payload['ledger_snapshot'] = _build_ledger_snapshot(result)
    balance_summary = _balance_summary_for_result(result)
    stats_summary = _strategy_stats_summary(result)
    ledger_open_size = 0.0 if result.local_position is None else float(result.local_position.ledger_open_size or 0.0)
    position_size = 0.0 if result.local_position is None else float(result.local_position.size or 0.0)
    payload['summary'] = {
        'symbol': result.regime_output.symbol,
        'execution_id': None if result.receipt is None else result.receipt.execution_id,
        'client_order_id': None if result.receipt is None else result.receipt.client_order_id,
        'order_id': None if result.receipt is None else result.receipt.order_id,
        'trade_ids': None if result.receipt is None else result.receipt.trade_ids,
        'entry_verified_hint': payload['verification_snapshot'].get('entry_verified_hint'),
        'entry_trade_confirmed': payload['verification_snapshot'].get('entry_trade_confirmed'),
        'entry_verification_attempt_count': payload['verification_snapshot'].get('entry_verification_attempt_count'),
        'theoretical_side': payload['theoretical_snapshot'].get('side'),
        'theoretical_size': payload['theoretical_snapshot'].get('size'),
        'theoretical_gross_pnl_proxy_usdt': payload['theoretical_snapshot'].get('theoretical_gross_pnl_proxy_usdt'),
        'execution_drag_proxy_usdt': payload['theoretical_snapshot'].get('execution_drag_proxy_usdt'),
        'open_leg_count': 0 if result.local_position is None else len(result.local_position.open_legs),
        'closed_leg_count': 0 if result.local_position is None else len(result.local_position.closed_legs),
        'pending_exit_leg_count': 0 if result.local_position is None or result.local_position.pending_exit is None else len(result.local_position.pending_exit.allocations),
        'ledger_open_size': ledger_open_size,
        'position_size': position_size,
        'position_ledger_diff': position_size - ledger_open_size,
        'runtime_mode': result.runtime_state.get('mode'),
        'active_strategy_version': result.active_strategy.get('version'),
        'active_strategy_label': (result.active_strategy.get('metadata') or {}).get('family'),
        'active_strategy_config_path': (result.active_strategy.get('metadata') or {}).get('config_path'),
        'regime': result.regime_output.final_decision.get('primary'),
        'confidence': result.regime_output.final_decision.get('confidence'),
        'plan_action': result.plan.action,
        'plan_account': result.plan.account,
        'plan_reason': result.plan.reason,
        'active_route': result.regime_output.route_decision.get('active_route'),
        'route_account': result.regime_output.route_decision.get('account'),
        'route_trade_enabled': result.regime_output.route_decision.get('trade_enabled'),
        'trade_enabled': result.decision_trace.pipeline_trade_enabled,
        'pipeline_entered': result.decision_trace.pipeline_entered,
        'submission_allowed': result.decision_trace.submission_allowed,
        'submission_attempted': result.decision_trace.submission_attempted,
        'allow_reason': result.decision_trace.allow_reason,
        'block_reason': result.decision_trace.block_reason,
        'diagnostics': list(result.decision_trace.diagnostics),
        'route_enabled': None if result.route_state is None else result.route_state.get('enabled'),
        'route_frozen_reason': None if result.route_state is None else result.route_state.get('frozen_reason'),
        'live_position_count': len(result.live_positions),
        'receipt_mode': None if result.receipt is None else result.receipt.mode,
        'receipt_accepted': None if result.receipt is None else result.receipt.accepted,
        'alignment_ok': None if result.reconcile_result is None else result.reconcile_result.alignment.ok,
        'policy_action': None if result.reconcile_result is None else result.reconcile_result.policy.action,
        'policy_reason': None if result.reconcile_result is None else result.reconcile_result.policy.reason,
        'account_metrics': build_account_metrics_from_cycle(receipt=result.receipt, reconcile_result=result.reconcile_result, balance_summary=balance_summary, local_position=result.local_position),
        'attribution_trade_count': payload['attribution_snapshot'].get('trade_count'),
        'attribution_fee_source': payload['attribution_snapshot'].get('fee_source'),
        'attribution_realized_pnl_source': payload['attribution_snapshot'].get('realized_pnl_source'),
        'attribution_equity_source': payload['attribution_snapshot'].get('equity_source'),
        'position_open_during_cycle': bool(position_size > 0.0 or ledger_open_size > 0.0),
        **stats_summary,
    }
    return payload


def _artifact_summary(artifact: dict[str, Any]) -> dict[str, Any]:
    return artifact.get('summary') if isinstance(artifact.get('summary'), dict) else {}


def _build_regime_local_artifact(result: ExecutionCycleResult, artifact: dict[str, Any]) -> dict[str, Any]:
    summary = _artifact_summary(artifact)
    return {
        'artifact_type': 'regime_local_cycle',
        'recorded_at': artifact.get('recorded_at'),
        'symbol': summary.get('symbol'),
        'runtime_mode': summary.get('runtime_mode'),
        'active_strategy_version': summary.get('active_strategy_version'),
        'active_strategy_label': summary.get('active_strategy_label'),
        'active_strategy_config_path': summary.get('active_strategy_config_path'),
        'final_regime': summary.get('regime'),
        'final_confidence': summary.get('confidence'),
        'background_regime': ((artifact.get('feature_snapshot') or {}).get('background_4h') or {}).get('regime'),
        'primary_regime': ((artifact.get('feature_snapshot') or {}).get('primary_15m') or {}).get('regime'),
        'override_regime': ((artifact.get('feature_snapshot') or {}).get('override_1m') or {}).get('regime'),
        'active_route': summary.get('active_route'),
        'route_account': summary.get('route_account'),
        'route_trade_enabled': summary.get('route_trade_enabled'),
        'plan_action': summary.get('plan_action'),
        'plan_account': summary.get('plan_account'),
        'plan_reason': summary.get('plan_reason'),
        'strategy_stats_eligible': summary.get('strategy_stats_eligible'),
        'strategy_stats_reason': summary.get('strategy_stats_reason'),
        'account_metrics': summary.get('account_metrics'),
        'feature_snapshot': artifact.get('feature_snapshot'),
        'theoretical_snapshot': artifact.get('theoretical_snapshot'),
    }


def _build_anomaly_artifact(result: ExecutionCycleResult, artifact: dict[str, Any]) -> dict[str, Any] | None:
    summary = _artifact_summary(artifact)
    if bool(summary.get('strategy_stats_eligible', True)):
        return None
    local = result.local_position
    meta = (local.meta if local is not None else {}) or {}
    recovery_type = meta.get('execution_recovery') or summary.get('strategy_stats_reason')
    return {
        'artifact_type': 'execution_anomaly',
        'recorded_at': artifact.get('recorded_at'),
        'runtime_mode': summary.get('runtime_mode'),
        'active_strategy_version': summary.get('active_strategy_version'),
        'active_strategy_label': summary.get('active_strategy_label'),
        'symbol': summary.get('symbol'),
        'account': summary.get('plan_account') or (None if result.receipt is None else result.receipt.account),
        'plan_action': summary.get('plan_action'),
        'execution_id': summary.get('execution_id'),
        'client_order_id': summary.get('client_order_id'),
        'order_id': summary.get('order_id'),
        'trade_ids': summary.get('trade_ids'),
        'attribution_trade_count': summary.get('attribution_trade_count'),
        'attribution_fee_source': summary.get('attribution_fee_source'),
        'attribution_realized_pnl_source': summary.get('attribution_realized_pnl_source'),
        'attribution_equity_source': summary.get('attribution_equity_source'),
        'theoretical_gross_pnl_proxy_usdt': summary.get('theoretical_gross_pnl_proxy_usdt'),
        'execution_drag_proxy_usdt': summary.get('execution_drag_proxy_usdt'),
        'strategy_stats_reason': summary.get('strategy_stats_reason'),
        'entry_verified_hint': summary.get('entry_verified_hint'),
        'entry_trade_confirmed': summary.get('entry_trade_confirmed'),
        'entry_verification_attempt_count': summary.get('entry_verification_attempt_count'),
        'execution_recovery': recovery_type,
        'execution_recovery_detail': meta.get('execution_recovery_detail'),
        'route_enabled': summary.get('route_enabled'),
        'route_frozen_reason': summary.get('route_frozen_reason'),
        'receipt_mode': summary.get('receipt_mode'),
        'receipt_accepted': summary.get('receipt_accepted'),
        'policy_action': summary.get('policy_action'),
        'policy_reason': summary.get('policy_reason'),
        'local_position_status': None if local is None else local.status.value,
        'local_position_reason': None if local is None else local.reason,
        'account_metrics': summary.get('account_metrics'),
    }


def persist_execution_artifact(result: ExecutionCycleResult) -> dict[str, Any]:
    artifact = build_execution_artifact(result)
    _append_jsonl(DETAILED_HISTORY_PATH, artifact)
    _append_jsonl(REGIME_HISTORY_PATH, _build_regime_local_artifact(result, artifact))
    anomaly = _build_anomaly_artifact(result, artifact)
    if anomaly is not None:
        _append_jsonl(ANOMALY_HISTORY_PATH, anomaly)
    return artifact


def build_active_strategy_execution_artifact(result: ActiveStrategyExecutionResult) -> dict[str, Any]:
    primary = build_execution_artifact(result.result)
    payload = {
        'artifact_type': 'active_strategy_execution_cycle',
        'recorded_at': datetime.now(UTC).isoformat(),
        'runtime_state': _sanitize_for_artifact(result.runtime_state),
        'active_strategy': _sanitize_for_artifact(result.active_strategy),
        'result': primary,
        'live_positions': _sanitize_for_artifact(result.live_positions),
    }
    return payload


def persist_active_strategy_execution_artifact(result: ActiveStrategyExecutionResult) -> dict[str, Any]:
    primary = persist_execution_artifact(result.result)
    artifact = build_active_strategy_execution_artifact(result)
    artifact['result'] = primary
    LATEST_PATH.write_text(json.dumps(artifact, indent=2, default=_json_default, ensure_ascii=False))
    _append_jsonl(HISTORY_PATH, artifact)
    return artifact


def main() -> None:
    pipeline = ExecutionPipeline()
    result = pipeline.run_cycle_active_strategy()
    artifact = persist_active_strategy_execution_artifact(result)
    print(json.dumps(artifact, indent=2, default=_json_default, ensure_ascii=False))


if __name__ == '__main__':
    main()
