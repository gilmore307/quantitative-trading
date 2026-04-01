from __future__ import annotations

from dataclasses import dataclass, asdict
from datetime import UTC, datetime
from typing import Any

from pathlib import Path
import json

from src.review.aggregator import aggregate_from_execution_history
from src.review.framework import ReviewWindow, build_review_plan
from src.review.performance import build_performance_snapshot
from src.routing.router import REGIME_ACCOUNT_MAP


def _row_pnl(row: dict[str, Any]) -> float:
    value = row.get('pnl_usdt')
    if value is not None:
        return float(value)
    realized = row.get('realized_pnl_usdt')
    unrealized = row.get('unrealized_pnl_usdt')
    if realized is not None or unrealized is not None:
        return float(realized or 0.0) + float(unrealized or 0.0)
    return 0.0


def _row_equity_change(row: dict[str, Any]) -> float:
    value = row.get('equity_change_usdt')
    return 0.0 if value is None else float(value)


def _row_funding(row: dict[str, Any]) -> float:
    value = row.get('funding_usdt')
    return 0.0 if value is None else float(value)


@dataclass(slots=True)
class ReviewReport:
    meta: dict[str, Any]
    sections: list[dict[str, Any]]
    metrics: dict[str, Any]
    parameter_candidates: dict[str, list[dict[str, Any]]]
    decisions: list[dict[str, Any]]
    notes: list[str]
    executive_summary: dict[str, Any]
    recommended_actions: list[dict[str, Any]]
    narrative_blocks: list[dict[str, Any]]


def _score_row(row: dict[str, Any]) -> tuple[float, float, float, float]:
    pnl = _row_pnl(row)
    equity_change = _row_equity_change(row)
    fee = float(row.get('fee_usdt') or 0.0)
    funding = _row_funding(row)
    return (pnl, equity_change, -fee, funding)


def _attribution_confidence(row: dict[str, Any]) -> str:
    fee = row.get('attribution_fee_source')
    realized = row.get('attribution_realized_pnl_source')
    equity = row.get('attribution_equity_source')
    strong = {'fill_aggregation', 'balance_summary'}
    if fee in strong and realized in strong and equity == 'balance_summary':
        return 'high'
    if fee or realized or equity:
        return 'medium'
    return 'low'


def _build_performance_summary(performance_snapshot: dict[str, Any]) -> dict[str, Any]:
    accounts = performance_snapshot.get('accounts', []) if isinstance(performance_snapshot, dict) else []
    ranked = [
        row for row in accounts
        if isinstance(row, dict) and any(
            row.get(key) is not None
            for key in ('pnl_usdt', 'realized_pnl_usdt', 'unrealized_pnl_usdt', 'equity_change_usdt', 'fee_usdt', 'funding_usdt')
        )
    ]
    ranked.sort(key=_score_row, reverse=True)

    def slim(row: dict[str, Any]) -> dict[str, Any]:
        theoretical_gross = None
        pnl = row.get('pnl_usdt')
        fee = row.get('fee_usdt')
        funding = row.get('funding_usdt')
        if pnl is not None or fee is not None or funding is not None:
            theoretical_gross = float(pnl or 0.0) + float(fee or 0.0) + float(funding or 0.0)
        realized_execution_drag = None if theoretical_gross is None or pnl is None else theoretical_gross - float(pnl)
        return {
            'account': row.get('account'),
            'pnl_usdt': row.get('pnl_usdt'),
            'equity_change_usdt': row.get('equity_change_usdt'),
            'fee_usdt': row.get('fee_usdt'),
            'funding_usdt': row.get('funding_usdt'),
            'realized_pnl_usdt': row.get('realized_pnl_usdt'),
            'unrealized_pnl_usdt': row.get('unrealized_pnl_usdt'),
            'equity_end_usdt': row.get('equity_end_usdt'),
            'funding_total_usdt': row.get('funding_total_usdt'),
            'trade_count': row.get('trade_count'),
            'exposure_time_pct': row.get('exposure_time_pct'),
            'attribution_fee_source': row.get('attribution_fee_source'),
            'attribution_realized_pnl_source': row.get('attribution_realized_pnl_source'),
            'attribution_equity_source': row.get('attribution_equity_source'),
            'attribution_confidence': _attribution_confidence(row),
            'theoretical_gross_pnl_proxy_usdt': theoretical_gross,
            'realized_execution_drag_usdt': realized_execution_drag,
            'source': row.get('source'),
        }

    leaderboard = [slim(row) for row in ranked]
    top = leaderboard[0] if leaderboard else None
    highest_fee = None
    fee_rows = [row for row in ranked if row.get('fee_usdt') is not None]
    if fee_rows:
        highest_fee = slim(max(fee_rows, key=lambda row: float(row.get('fee_usdt') or 0.0)))
    highest_exposure = None
    exposure_rows = [row for row in ranked if row.get('exposure_time_pct') is not None]
    if exposure_rows:
        highest_exposure = slim(max(exposure_rows, key=lambda row: float(row.get('exposure_time_pct') or 0.0)))

    execution_deviation = None
    if top is not None:
        execution_deviation = {
            'account': top.get('account'),
            'actual_pnl_usdt': top.get('pnl_usdt'),
            'theoretical_gross_pnl_proxy_usdt': top.get('theoretical_gross_pnl_proxy_usdt'),
            'realized_execution_drag_usdt': top.get('realized_execution_drag_usdt'),
            'fee_usdt': top.get('fee_usdt'),
            'funding_usdt': top.get('funding_usdt'),
            'trade_count': top.get('trade_count'),
            'exposure_time_pct': top.get('exposure_time_pct'),
            'attribution_confidence': top.get('attribution_confidence'),
        }

    insights: list[str] = []
    if top is not None:
        insights.append(f"active_live_pnl:{top.get('pnl_usdt')}")
    if execution_deviation is not None and execution_deviation.get('realized_execution_drag_usdt') is not None:
        insights.append(f"execution_drag:{execution_deviation.get('realized_execution_drag_usdt')}")
    if highest_fee is not None:
        insights.append(f"highest_fee_drag:{highest_fee['account']}")
    if highest_exposure is not None and float(highest_exposure.get('exposure_time_pct') or 0.0) >= 80.0:
        insights.append(f"high_exposure:{highest_exposure['account']}")

    return {
        'leaderboard': leaderboard,
        'top_account': top,
        'highest_fee_drag_account': highest_fee,
        'highest_exposure_account': highest_exposure,
        'execution_deviation': execution_deviation,
        'insights': insights,
    }


def _load_history_rows(path: str | None) -> list[dict[str, Any]]:
    if not path:
        return []
    p = Path(path)
    if not p.exists():
        return []
    rows: list[dict[str, Any]] = []
    files = [p] if p.is_file() else sorted(child for child in p.glob('*.jsonl') if child.is_file())
    for file_path in files:
        for line in file_path.read_text(encoding='utf-8').splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                rows.append(json.loads(line))
            except Exception:
                continue
    return rows


def _build_regime_local_summary(history_rows: list[dict[str, Any]]) -> dict[str, Any]:
    buckets: dict[str, dict[str, Any]] = {}
    for row in history_rows:
        summary = row.get('summary') if isinstance(row.get('summary'), dict) else row
        regime = str(summary.get('regime') or summary.get('final_regime') or 'unknown')
        route_family = str(summary.get('route_strategy_family') or 'none')
        eligible = bool(summary.get('strategy_stats_eligible', False))
        account_metrics = summary.get('account_metrics') if isinstance(summary.get('account_metrics'), dict) else {}
        plan_account = summary.get('plan_account') or summary.get('route_account') or (next(iter(account_metrics.keys())) if account_metrics else None)
        pnl = 0.0
        if plan_account in account_metrics and isinstance(account_metrics.get(plan_account), dict):
            pnl = _row_pnl(account_metrics[plan_account])
        bucket = buckets.setdefault(regime, {
            'regime': regime,
            'total_cycles': 0,
            'clean_cycles': 0,
            'excluded_cycles': 0,
            'clean_pnl_usdt': 0.0,
            'excluded_pnl_usdt': 0.0,
            'route_families': {},
        })
        bucket['total_cycles'] += 1
        bucket['route_families'][route_family] = bucket['route_families'].get(route_family, 0) + 1
        if eligible:
            bucket['clean_cycles'] += 1
            bucket['clean_pnl_usdt'] = round(float(bucket['clean_pnl_usdt']) + pnl, 10)
        else:
            bucket['excluded_cycles'] += 1
            bucket['excluded_pnl_usdt'] = round(float(bucket['excluded_pnl_usdt']) + pnl, 10)
    rows = []
    for regime, bucket in buckets.items():
        dominant_route = None
        if bucket['route_families']:
            dominant_route = sorted(bucket['route_families'].items(), key=lambda item: (-item[1], item[0]))[0][0]
        rows.append({
            'regime': regime,
            'total_cycles': bucket['total_cycles'],
            'clean_cycles': bucket['clean_cycles'],
            'excluded_cycles': bucket['excluded_cycles'],
            'clean_pnl_usdt': bucket['clean_pnl_usdt'],
            'excluded_pnl_usdt': bucket['excluded_pnl_usdt'],
            'dominant_route_family': dominant_route,
            'route_families': bucket['route_families'],
        })
    rows.sort(key=lambda item: (-int(item['total_cycles']), item['regime']))
    return {'rows': rows, 'status': 'ready' if rows else 'placeholder'}


def _build_overlap_summary(history_rows: list[dict[str, Any]]) -> dict[str, Any]:
    rows = []
    for row in history_rows:
        feature_snapshot = row.get('feature_snapshot') if isinstance(row.get('feature_snapshot'), dict) else {}
        final_regime = row.get('final_regime') or ((row.get('summary') or {}).get('regime') if isinstance(row.get('summary'), dict) else None)
        primary = feature_snapshot.get('primary_15m') if isinstance(feature_snapshot.get('primary_15m'), dict) else {}
        scores = primary.get('scores') if isinstance(primary.get('scores'), dict) else {}
        if not scores:
            continue
        ranked = sorted(scores.items(), key=lambda item: item[1], reverse=True)
        top_name, top_score = ranked[0]
        second_name, second_score = ranked[1] if len(ranked) > 1 else (None, 0.0)
        gap = round(float(top_score) - float(second_score), 10)
        if gap > 0.15:
            continue
        rows.append({'final_regime': final_regime or top_name, 'top_regime': top_name, 'top_score': top_score, 'runner_up_regime': second_name, 'runner_up_score': second_score, 'score_gap': gap})
    rows.sort(key=lambda item: (item['score_gap'], str(item['final_regime'])))
    return {'rows': rows[:50], 'status': 'ready' if rows else 'placeholder'}


def _build_mapping_validity_summary(history_rows: list[dict[str, Any]]) -> dict[str, Any]:
    expected_map = {str(regime.value): account for regime, account in REGIME_ACCOUNT_MAP.items()}
    buckets: dict[str, dict[str, Any]] = {}
    for row in history_rows:
        summary = row.get('summary') if isinstance(row.get('summary'), dict) else row
        regime = str(summary.get('regime') or summary.get('final_regime') or 'unknown')
        route_account = summary.get('route_account') or summary.get('plan_account')
        expected_account = expected_map.get(regime)
        bucket = buckets.setdefault(regime, {'regime': regime, 'expected_account': expected_account, 'total_cycles': 0, 'matched_cycles': 0, 'routed_none_cycles': 0, 'route_counts': {}})
        bucket['total_cycles'] += 1
        route_key = 'none' if route_account is None else str(route_account)
        bucket['route_counts'][route_key] = bucket['route_counts'].get(route_key, 0) + 1
        if route_account is None:
            bucket['routed_none_cycles'] += 1
        if route_account == expected_account:
            bucket['matched_cycles'] += 1
    rows = []
    for regime, bucket in buckets.items():
        total = int(bucket['total_cycles'])
        matched = int(bucket['matched_cycles'])
        match_rate = 0.0 if total <= 0 else round((matched / total) * 100.0, 4)
        dominant_route = sorted(bucket['route_counts'].items(), key=lambda item: (-item[1], item[0]))[0][0] if bucket['route_counts'] else None
        rows.append({'regime': regime, 'expected_account': bucket['expected_account'], 'dominant_route': dominant_route, 'total_cycles': total, 'matched_cycles': matched, 'match_rate_pct': match_rate, 'routed_none_cycles': int(bucket['routed_none_cycles']), 'route_counts': bucket['route_counts']})
    rows.sort(key=lambda item: (-int(item['total_cycles']), item['regime']))
    return {'rows': rows, 'status': 'ready' if rows else 'placeholder'}


def _build_execution_quality_summary(history_rows: list[dict[str, Any]]) -> dict[str, Any]:
    clean = 0
    excluded = 0
    reasons: dict[str, int] = {}
    confirmation_modes = {'trade_confirmed': 0, 'trade_ids_confirmed': 0, 'position_confirmed': 0, 'other_clean': 0}
    excluded_pnl_usdt = 0.0
    excluded_rows: list[dict[str, Any]] = []
    anomaly_groups: dict[str, dict[str, Any]] = {}
    for row in history_rows:
        summary = row.get('summary') if isinstance(row.get('summary'), dict) else {}
        eligible = bool(summary.get('strategy_stats_eligible', False))
        reason = str(summary.get('strategy_stats_reason') or ('clean_execution' if eligible else 'unknown'))
        if eligible:
            clean += 1
            local_reason = str((row.get('verification_snapshot') or {}).get('local_position_reason') or '')
            if local_reason == 'exchange_position_trade_confirmed':
                confirmation_modes['trade_confirmed'] += 1
            elif local_reason == 'exchange_position_trade_ids_confirmed':
                confirmation_modes['trade_ids_confirmed'] += 1
            elif local_reason == 'exchange_position_confirmed':
                confirmation_modes['position_confirmed'] += 1
            else:
                confirmation_modes['other_clean'] += 1
            continue
        excluded += 1
        reasons[reason] = reasons.get(reason, 0) + 1
        metrics = summary.get('account_metrics') if isinstance(summary.get('account_metrics'), dict) else {}
        account = summary.get('plan_account') or (next(iter(metrics.keys())) if metrics else None)
        pnl = 0.0
        if account in metrics and isinstance(metrics.get(account), dict):
            pnl = _row_pnl(metrics[account])
        excluded_pnl_usdt += pnl
        sample = {'account': account, 'reason': reason, 'pnl_usdt': pnl, 'entry_verified_hint': summary.get('entry_verified_hint'), 'entry_trade_confirmed': summary.get('entry_trade_confirmed')}
        excluded_rows.append(sample)
        group = anomaly_groups.setdefault(reason, {'reason': reason, 'count': 0, 'pnl_usdt': 0.0, 'accounts': [], 'samples': []})
        group['count'] += 1
        group['pnl_usdt'] = round(float(group['pnl_usdt']) + pnl, 10)
        if account is not None and account not in group['accounts']:
            group['accounts'].append(account)
        if len(group['samples']) < 5:
            group['samples'].append(sample)
    top_excluded_reasons = [{'reason': key, 'count': value} for key, value in sorted(reasons.items(), key=lambda item: (-item[1], item[0]))]
    anomaly_breakdown = sorted(anomaly_groups.values(), key=lambda item: (-int(item['count']), str(item['reason'])))
    confirmation_breakdown = [{'mode': key, 'count': value} for key, value in confirmation_modes.items() if value > 0]
    return {'clean_trade_count': clean, 'excluded_trade_count': excluded, 'excluded_pnl_usdt': round(excluded_pnl_usdt, 10), 'top_excluded_reasons': top_excluded_reasons, 'excluded_samples': excluded_rows[:20], 'anomaly_breakdown': anomaly_breakdown, 'confirmation_breakdown': confirmation_breakdown, 'status': 'ready' if history_rows else 'placeholder'}


def _build_execution_deviation_summary(performance_summary: dict[str, Any]) -> dict[str, Any]:
    row = performance_summary.get('execution_deviation') if isinstance(performance_summary, dict) else None
    if not isinstance(row, dict):
        return {'status': 'placeholder', 'row': None}
    return {'status': 'ready', 'row': row}


def _build_regime_local_section(regime_local: dict[str, Any]) -> dict[str, Any]:
    rows = regime_local.get('rows', []) if isinstance(regime_local, dict) else []
    return {'key': 'regime_local_review', 'title': 'Regime-Local Review', 'status': regime_local.get('status', 'placeholder'), 'items': ([{'kind': 'regime_rows', 'rows': rows}] if rows else []), 'highlights': [f"{row.get('regime')}:clean={row.get('clean_cycles')}/excluded={row.get('excluded_cycles')}" for row in rows[:5]]}


def _build_overlap_section(overlap: dict[str, Any]) -> dict[str, Any]:
    rows = overlap.get('rows', []) if isinstance(overlap, dict) else []
    return {'key': 'overlap_review', 'title': 'Regime Overlap Review', 'status': overlap.get('status', 'placeholder'), 'items': ([{'kind': 'overlap_rows', 'rows': rows}] if rows else []), 'highlights': [f"{row.get('final_regime')}: top={row.get('top_regime')} runner_up={row.get('runner_up_regime')} gap={row.get('score_gap')}" for row in rows[:6]]}


def _build_mapping_validity_section(mapping_validity: dict[str, Any]) -> dict[str, Any]:
    rows = mapping_validity.get('rows', []) if isinstance(mapping_validity, dict) else []
    return {'key': 'mapping_validity_review', 'title': 'Mapping Validity Review', 'status': mapping_validity.get('status', 'placeholder'), 'items': ([{'kind': 'mapping_rows', 'rows': rows}] if rows else []), 'highlights': [f"{row.get('regime')}:expected={row.get('expected_account')} dominant={row.get('dominant_route')} match={row.get('match_rate_pct')}%" for row in rows[:6]]}


def _build_execution_quality_section(execution_quality: dict[str, Any]) -> dict[str, Any]:
    items = []
    if execution_quality.get('anomaly_breakdown'):
        items.append({'kind': 'anomaly_breakdown', 'rows': execution_quality.get('anomaly_breakdown', [])})
    if execution_quality.get('top_excluded_reasons'):
        items.append({'kind': 'excluded_reasons', 'rows': execution_quality.get('top_excluded_reasons', [])})
    if execution_quality.get('excluded_samples'):
        items.append({'kind': 'excluded_samples', 'rows': execution_quality.get('excluded_samples', [])})
    highlights = []
    if execution_quality.get('excluded_trade_count'):
        highlights.append(f"excluded_trade_count:{execution_quality.get('excluded_trade_count')}")
    if execution_quality.get('excluded_pnl_usdt'):
        highlights.append(f"excluded_pnl_usdt:{execution_quality.get('excluded_pnl_usdt')}")
    return {'key': 'execution_quality', 'title': 'Execution Quality', 'status': execution_quality.get('status', 'placeholder'), 'items': items, 'highlights': highlights}


def _build_live_performance_section(performance_summary: dict[str, Any]) -> dict[str, Any]:
    leaderboard = performance_summary.get('leaderboard', []) if isinstance(performance_summary, dict) else []
    top = performance_summary.get('top_account') if isinstance(performance_summary, dict) else None
    highlights = [f"active_live_pnl:{top.get('pnl_usdt')}" for top in [top] if top is not None]
    return {'key': 'live_performance_summary', 'title': 'Live Performance Summary', 'status': ('ready' if leaderboard else 'placeholder'), 'items': ([{'kind': 'leaderboard', 'rows': leaderboard}] if leaderboard else []), 'highlights': highlights}


def _build_execution_deviation_section(execution_deviation: dict[str, Any]) -> dict[str, Any]:
    row = execution_deviation.get('row') if isinstance(execution_deviation, dict) else None
    highlights = []
    if isinstance(row, dict) and row.get('realized_execution_drag_usdt') is not None:
        highlights.append(f"execution_drag_usdt:{row.get('realized_execution_drag_usdt')}")
    return {'key': 'execution_deviation_review', 'title': 'Theoretical vs Actual Execution Deviation', 'status': execution_deviation.get('status', 'placeholder'), 'items': ([{'kind': 'execution_deviation', 'row': row}] if isinstance(row, dict) else []), 'highlights': highlights}


def _build_execution_improvement_section(performance_summary: dict[str, Any]) -> dict[str, Any]:
    items: list[dict[str, Any]] = []
    highest_fee = performance_summary.get('highest_fee_drag_account') if isinstance(performance_summary, dict) else None
    highest_exposure = performance_summary.get('highest_exposure_account') if isinstance(performance_summary, dict) else None
    deviation = performance_summary.get('execution_deviation') if isinstance(performance_summary, dict) else None

    if highest_fee is not None:
        items.append({'kind': 'improvement', 'name': 'trade_frequency_review', 'status': 'review', 'reason': f"highest fee drag observed on {highest_fee.get('account')}; check whether live execution frequency is too high for the promoted strategy", 'target_account': highest_fee.get('account'), 'evidence': highest_fee})
    if highest_exposure is not None and float(highest_exposure.get('exposure_time_pct') or 0.0) >= 80.0:
        items.append({'kind': 'improvement', 'name': 'position_drift_review', 'status': 'review', 'reason': f"exposure stayed elevated on {highest_exposure.get('account')}; verify theoretical vs actual position drift", 'target_account': highest_exposure.get('account'), 'evidence': highest_exposure})
    if isinstance(deviation, dict) and deviation.get('realized_execution_drag_usdt') is not None and float(deviation.get('realized_execution_drag_usdt') or 0.0) > 0.0:
        items.append({'kind': 'improvement', 'name': 'execution_drag_review', 'status': 'review', 'reason': f"actual pnl trails theoretical gross pnl proxy by {deviation.get('realized_execution_drag_usdt')} USDT; inspect fees, funding, slippage, and fill quality", 'target_account': deviation.get('account'), 'evidence': deviation})

    return {'key': 'execution_improvement_review', 'title': 'Execution Improvement Review', 'status': 'ready' if items else 'placeholder', 'items': items}


def _build_executive_summary(meta: dict[str, Any], performance_summary: dict[str, Any], execution_improvement_section: dict[str, Any], execution_quality: dict[str, Any], execution_deviation: dict[str, Any]) -> dict[str, Any]:
    top = performance_summary.get('top_account') if isinstance(performance_summary, dict) else None
    candidate_count = len(execution_improvement_section.get('items', [])) if isinstance(execution_improvement_section, dict) else 0
    deviation_row = execution_deviation.get('row') if isinstance(execution_deviation, dict) else None
    bullets: list[str] = []
    if top is not None:
        bullets.append(f"Actual live pnl: {top.get('pnl_usdt')} USDT")
    if isinstance(deviation_row, dict):
        bullets.append(f"Theoretical gross pnl proxy: {deviation_row.get('theoretical_gross_pnl_proxy_usdt')} USDT")
        bullets.append(f"Execution drag (fees/funding/slippage proxy): {deviation_row.get('realized_execution_drag_usdt')} USDT")
    if candidate_count:
        bullets.append(f"Execution improvement items flagged: {candidate_count}")
    if execution_quality.get('status') == 'ready':
        bullets.append(f"Clean vs excluded trades: {execution_quality.get('clean_trade_count', 0)} clean / {execution_quality.get('excluded_trade_count', 0)} excluded")
        if execution_quality.get('excluded_trade_count', 0):
            bullets.append(f"Excluded execution-impact pnl: {execution_quality.get('excluded_pnl_usdt')} USDT")
    return {'label': meta.get('label'), 'cadence': meta.get('cadence'), 'window_start': meta.get('window_start'), 'window_end': meta.get('window_end'), 'bullets': bullets, 'status': 'ready' if bullets else 'placeholder'}


def _build_recommended_actions(execution_improvement_section: dict[str, Any]) -> list[dict[str, Any]]:
    return [{'title': f"Review {item.get('name')}", 'priority': item.get('status') or 'review', 'target_account': item.get('target_account'), 'reason': item.get('reason')} for item in execution_improvement_section.get('items', []) if item.get('kind') == 'improvement'] if isinstance(execution_improvement_section, dict) else []


def _build_narrative_blocks(executive_summary: dict[str, Any], sections: list[dict[str, Any]]) -> list[dict[str, Any]]:
    blocks: list[dict[str, Any]] = []
    if executive_summary.get('bullets'):
        blocks.append({'key': 'executive_summary', 'title': 'Executive Summary', 'lines': executive_summary['bullets']})
    for section in sections:
        key = section.get('key')
        if key == 'live_performance_summary' and section.get('status') == 'ready':
            leaderboard = next((item.get('rows') for item in section.get('items', []) if item.get('kind') == 'leaderboard'), [])
            lines = [f"actual pnl={row.get('pnl_usdt')} fee={row.get('fee_usdt')} funding={row.get('funding_usdt')} exposure={row.get('exposure_time_pct')}" for row in leaderboard[:1]]
            blocks.append({'key': key, 'title': section.get('title'), 'lines': lines})
        elif key == 'execution_deviation_review' and section.get('status') == 'ready':
            row = next((item.get('row') for item in section.get('items', []) if item.get('kind') == 'execution_deviation'), None)
            if isinstance(row, dict):
                blocks.append({'key': key, 'title': section.get('title'), 'lines': [f"theoretical gross pnl proxy={row.get('theoretical_gross_pnl_proxy_usdt')}", f"actual pnl={row.get('actual_pnl_usdt')}", f"execution drag={row.get('realized_execution_drag_usdt')}", f"fee={row.get('fee_usdt')} funding={row.get('funding_usdt')} trade_count={row.get('trade_count')}"]})
        elif key == 'execution_improvement_review' and section.get('status') == 'ready':
            blocks.append({'key': key, 'title': section.get('title'), 'lines': [f"{item.get('name')} [{item.get('status')}]: {item.get('reason')}" for item in section.get('items', []) if item.get('kind') == 'improvement']})
        elif key == 'execution_quality' and section.get('status') == 'ready':
            lines = []
            for item in section.get('items', []):
                if item.get('kind') == 'anomaly_breakdown':
                    for row in item.get('rows', [])[:5]:
                        lines.append(f"anomaly {row.get('reason')}: count={row.get('count')} pnl={row.get('pnl_usdt')} accounts={','.join(row.get('accounts', []))}")
                elif item.get('kind') == 'excluded_reasons':
                    for row in item.get('rows', [])[:5]:
                        lines.append(f"excluded_reason {row.get('reason')}: {row.get('count')}")
            blocks.append({'key': key, 'title': section.get('title'), 'lines': lines})
    return blocks


def build_report_scaffold(window: ReviewWindow, metrics_by_account: dict[str, dict[str, Any]] | None = None, history_path: str | None = None) -> dict[str, Any]:
    plan = build_review_plan(window)
    cadence = plan['cadence']
    aggregated_metrics = metrics_by_account
    history_rows: list[dict[str, Any]] = []
    if history_path is not None:
        aggregated_metrics = aggregate_from_execution_history(history_path, metrics_by_account, window_start=window.window_start, window_end=window.window_end)
        history_rows = _load_history_rows(history_path)
    performance_snapshot = build_performance_snapshot(aggregated_metrics)
    performance_summary = _build_performance_summary(performance_snapshot)
    regime_local = _build_regime_local_summary(history_rows)
    mapping_validity = _build_mapping_validity_summary(history_rows)
    overlap = _build_overlap_summary(history_rows)
    execution_quality = _build_execution_quality_summary(history_rows)
    execution_deviation = _build_execution_deviation_summary(performance_summary)
    execution_improvement_section = _build_execution_improvement_section(performance_summary)
    sections = [{'key': 'market_regime_summary', 'title': 'Market Regime Summary', 'status': 'placeholder', 'items': []}, _build_live_performance_section(performance_summary), _build_execution_deviation_section(execution_deviation), _build_regime_local_section(regime_local), _build_mapping_validity_section(mapping_validity), _build_overlap_section(overlap), _build_execution_quality_section(execution_quality), execution_improvement_section]
    if cadence == 'quarterly':
        sections.append({'key': 'structural_review', 'title': 'Structural Review', 'status': 'placeholder', 'items': []})
    meta = {'cadence': cadence, 'label': plan['label'], 'window_start': plan['window_start'], 'window_end': plan['window_end'], 'generated_at': datetime.now(UTC).isoformat(), 'focus_areas': plan['focus_areas'], 'adjustment_policy': plan['adjustment_policy']}
    executive_summary = _build_executive_summary(meta, performance_summary, execution_improvement_section, execution_quality, execution_deviation)
    recommended_actions = _build_recommended_actions(execution_improvement_section)
    narrative_blocks = _build_narrative_blocks(executive_summary, sections)
    report = ReviewReport(meta=meta, sections=sections, metrics={'performance': performance_snapshot, 'performance_summary': performance_summary, 'execution_deviation': execution_deviation, 'regime_local': regime_local, 'mapping_validity': mapping_validity, 'overlap': overlap, 'execution_quality': execution_quality, 'risk': [], 'fees': [], 'regime_quality': []}, parameter_candidates={'auto_candidate_params': [], 'discuss_first_params': [], 'structural_params': []}, decisions=[], notes=plan['notes'], executive_summary=executive_summary, recommended_actions=recommended_actions, narrative_blocks=narrative_blocks)
    return asdict(report)
