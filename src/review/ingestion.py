from __future__ import annotations

from typing import Any

from src.review.performance import DEFAULT_COMPARE_ACCOUNTS, FLAT_COMPARE_ALIAS, ACTIVE_LIVE_ALIAS


CANONICAL_NUMERIC_FIELDS = (
    'realized_pnl_usdt',
    'unrealized_pnl_usdt',
    'unrealized_pnl_start_usdt',
    'unrealized_pnl_change_usdt',
    'pnl_usdt',
    'equity_usdt',
    'equity_start_usdt',
    'equity_end_usdt',
    'equity_change_usdt',
    'fee_usdt',
    'funding_usdt',
    'funding_total_usdt',
    'trade_count',
    'exposure_time_pct',
    'max_drawdown_pct',
)

ATTRIBUTION_FIELDS = (
    'attribution_fee_source',
    'attribution_realized_pnl_source',
    'attribution_equity_source',
)


def _safe_float(value: Any) -> float | None:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _merge_metric_fields(target: dict[str, float], raw: dict[str, Any], *, overwrite: bool = True) -> None:
    for key in CANONICAL_NUMERIC_FIELDS:
        value = _safe_float(raw.get(key))
        if value is None:
            continue
        if overwrite or key not in target:
            target[key] = value

    if 'pnl_usdt' not in target:
        total = _safe_float(raw.get('total_pnl_usdt'))
        if total is not None:
            target['pnl_usdt'] = total
    if 'pnl_usdt' not in target:
        realized = _safe_float(raw.get('realized_pnl_usdt'))
        unrealized = _safe_float(raw.get('unrealized_pnl_usdt'))
        if realized is not None or unrealized is not None:
            target['pnl_usdt'] = float(realized or 0.0) + float(unrealized or 0.0)

    if 'equity_usdt' not in target:
        equity_end = _safe_float(raw.get('equity_end_usdt'))
        if equity_end is not None:
            target['equity_usdt'] = equity_end
    if 'equity_end_usdt' not in target:
        equity = _safe_float(raw.get('equity_usdt'))
        if equity is not None:
            target['equity_end_usdt'] = equity

    if 'equity_change_usdt' not in target:
        start = _safe_float(raw.get('equity_start_usdt'))
        end = _safe_float(raw.get('equity_end_usdt'))
        if start is None:
            start = _safe_float(raw.get('equity_start'))
        if end is None:
            end = _safe_float(raw.get('equity_usdt'))
        if start is not None and end is not None:
            target['equity_change_usdt'] = end - start

    for key in ATTRIBUTION_FIELDS:
        value = raw.get(key)
        if value is None:
            continue
        if overwrite or key not in target:
            target[key] = str(value)


def canonicalize_history_row(row: dict[str, Any]) -> dict[str, dict[str, float]]:
    """Extract canonical performance hints from one execution artifact row.

    The current live architecture is single-active-model oriented, so any
    live execution-side metrics are aggregated under `active_live` rather than
    a standing family-account matrix.
    """

    metrics: dict[str, dict[str, float]] = {}

    receipt = row.get('receipt') or {}
    receipt_raw = receipt.get('raw') if isinstance(receipt, dict) else {}
    if not isinstance(receipt_raw, dict):
        receipt_raw = {}
    if isinstance(receipt_raw, dict) and receipt_raw:
        target = metrics.setdefault(ACTIVE_LIVE_ALIAS, {})
        _merge_metric_fields(target, receipt_raw, overwrite=False)

    summary = row.get('summary') or {}
    summary_metrics = summary.get('account_metrics') if isinstance(summary, dict) else None
    if isinstance(summary_metrics, dict):
        for _, raw in summary_metrics.items():
            if not isinstance(raw, dict):
                continue
            target = metrics.setdefault(ACTIVE_LIVE_ALIAS, {})
            _merge_metric_fields(target, raw, overwrite=True)

    primary_summary = None
    if isinstance(row.get('summary'), dict) and isinstance(row['summary'].get('primary_summary'), dict):
        primary_summary = row['summary']['primary_summary']
    elif isinstance(row.get('result'), dict) and isinstance(row['result'].get('summary'), dict):
        primary_summary = row['result']['summary']
    if isinstance(primary_summary, dict):
        target = metrics.setdefault(ACTIVE_LIVE_ALIAS, {})
        _merge_metric_fields(target, primary_summary, overwrite=False)

    metrics.setdefault(FLAT_COMPARE_ALIAS, {})
    return metrics
