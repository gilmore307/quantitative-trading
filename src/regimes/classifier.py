from __future__ import annotations

from typing import Protocol, Any

from src.features.models import FeatureSnapshot
from src.regimes.models import Regime, RegimeDecision


class RegimeClassifier(Protocol):
    def classify(self, snapshot: FeatureSnapshot) -> RegimeDecision:
        ...


class RuleBasedRegimeClassifier:
    """Parameterized runtime label calculator.

    Labels are still computed inside the runtime, but the thresholds/weights are
    expected to come from external model inputs rather than being permanently
    hard-coded into the runtime architecture.
    """

    REQUIRED_KEYS = {
        'trend_adx_low', 'trend_adx_high', 'trend_vwap_z_min', 'trend_vwap_z_scale',
        'range_adx_cap', 'range_adx_window', 'range_vwap_z_min', 'range_vwap_z_max',
        'compression_bandwidth_cap', 'compression_bandwidth_window', 'compression_realized_vol_scale',
        'crowded_funding_floor', 'crowded_funding_window', 'shock_activation_threshold',
        'crowded_activation_threshold', 'label_activation_threshold', 'label_gap_threshold',
    }

    def __init__(self, parameters: dict[str, Any] | None = None):
        self.parameters = parameters or {}
        missing = sorted(key for key in self.REQUIRED_KEYS if key not in self.parameters)
        if missing:
            raise RuntimeError(f"missing_label_parameters:{','.join(missing)}")

    def _value(self, key: str, default: float) -> float:
        value = self.parameters.get(key, default)
        try:
            return float(value)
        except (TypeError, ValueError):
            return float(default)

    def _clamp(self, value: float, low: float = 0.0, high: float = 1.0) -> float:
        return max(low, min(high, value))

    def _score_trend(self, snapshot: FeatureSnapshot) -> tuple[float, list[str]]:
        score = 0.0
        reasons: list[str] = []
        adx_low = self._value('trend_adx_low', 18.0)
        adx_high = self._value('trend_adx_high', 35.0)
        if snapshot.adx is not None:
            adx_score = self._clamp((snapshot.adx - adx_low) / max(1e-6, adx_high - adx_low))
            score += 0.35 * adx_score
            if adx_score >= 0.6:
                reasons.append('adx_supports_trend')
        if snapshot.ema20_slope is not None and snapshot.ema50_slope is not None and snapshot.ema20_slope * snapshot.ema50_slope > 0:
            slope_mag = abs(snapshot.ema20_slope) + abs(snapshot.ema50_slope)
            score += 0.45 * max(0.4, self._clamp(slope_mag))
            reasons.append('ema_slopes_aligned')
        if snapshot.vwap_deviation_z is not None and abs(snapshot.vwap_deviation_z) >= self._value('trend_vwap_z_min', 0.5):
            score += 0.20 * self._clamp(abs(snapshot.vwap_deviation_z) / self._value('trend_vwap_z_scale', 2.5))
            reasons.append('directional_vwap_extension')
        return self._clamp(score), reasons

    def _score_range(self, snapshot: FeatureSnapshot) -> tuple[float, list[str]]:
        score = 0.0
        reasons: list[str] = []
        if snapshot.adx is not None:
            low_adx_score = self._clamp((self._value('range_adx_cap', 22.0) - snapshot.adx) / self._value('range_adx_window', 12.0))
            score += 0.40 * low_adx_score
            if low_adx_score >= 0.5:
                reasons.append('low_adx_supports_range')
        if snapshot.vwap_deviation_z is not None:
            z = abs(snapshot.vwap_deviation_z)
            z_min = self._value('range_vwap_z_min', 0.5)
            z_max = self._value('range_vwap_z_max', 2.5)
            z_mid = (z_min + z_max) / 2.0
            if z_min <= z <= z_max:
                score += 0.35 * self._clamp((z_max - abs(z - z_mid)) / max(1e-6, z_mid))
                reasons.append('reversion_distance_present')
        if snapshot.bollinger_bandwidth_pct is not None and snapshot.bollinger_bandwidth_pct > self._value('range_bandwidth_floor', 0.15):
            score += 0.25 * self._clamp((self._value('range_bandwidth_cap', 0.35) - min(snapshot.bollinger_bandwidth_pct, self._value('range_bandwidth_cap', 0.35))) / self._value('range_bandwidth_window', 0.20))
            reasons.append('bandwidth_not_extremely_compressed')
        return self._clamp(score), reasons

    def _score_compression(self, snapshot: FeatureSnapshot) -> tuple[float, list[str]]:
        score = 0.0
        reasons: list[str] = []
        if snapshot.bollinger_bandwidth_pct is not None:
            width_score = self._clamp((self._value('compression_bandwidth_cap', 0.20) - snapshot.bollinger_bandwidth_pct) / self._value('compression_bandwidth_window', 0.20))
            score += 0.50 * width_score
            if width_score >= 0.5:
                reasons.append('low_bandwidth')
        if snapshot.realized_vol_pct is not None:
            vol_score = self._clamp(1.0 - snapshot.realized_vol_pct / self._value('compression_realized_vol_scale', 1.0))
            score += 0.30 * vol_score
            if vol_score >= 0.5:
                reasons.append('low_realized_vol')
        if snapshot.adx is not None and snapshot.adx < self._value('compression_adx_cap', 22.0):
            score += 0.20 * self._clamp((self._value('compression_adx_cap', 22.0) - snapshot.adx) / self._value('compression_adx_window', 12.0))
            reasons.append('non_trending_structure')
        return self._clamp(score), reasons

    def _score_crowded(self, snapshot: FeatureSnapshot) -> tuple[float, list[str]]:
        score = 0.0
        reasons: list[str] = []
        if snapshot.funding_pctile is not None:
            funding_extreme = max(snapshot.funding_pctile, 1.0 - snapshot.funding_pctile)
            score += 0.30 * self._clamp((funding_extreme - self._value('crowded_funding_floor', 0.80)) / self._value('crowded_funding_window', 0.20))
            if funding_extreme >= self._value('crowded_funding_reason_floor', 0.90):
                reasons.append('extreme_funding')
        if snapshot.oi_accel is not None:
            score += 0.30 * self._clamp(snapshot.oi_accel / self._value('crowded_oi_accel_scale', 1.0))
            if snapshot.oi_accel >= self._value('crowded_oi_reason_floor', 0.5):
                reasons.append('oi_acceleration')
        if snapshot.basis_deviation_pct is not None:
            score += 0.20 * self._clamp(abs(snapshot.basis_deviation_pct) / self._value('crowded_basis_scale', 0.03))
            if abs(snapshot.basis_deviation_pct) >= self._value('crowded_basis_reason_floor', 0.01):
                reasons.append('basis_extension')
        if snapshot.vwap_deviation_z is not None:
            score += 0.20 * self._clamp(abs(snapshot.vwap_deviation_z) / self._value('crowded_vwap_scale', 3.0))
            if abs(snapshot.vwap_deviation_z) >= self._value('crowded_vwap_reason_floor', 1.5):
                reasons.append('price_extension')
        return self._clamp(score), reasons

    def _score_shock(self, snapshot: FeatureSnapshot) -> tuple[float, list[str]]:
        score = 0.0
        reasons: list[str] = []
        if snapshot.realized_vol_pct is not None:
            vol_component = self._clamp((snapshot.realized_vol_pct - self._value('shock_realized_vol_floor', 0.75)) / self._value('shock_realized_vol_window', 0.25))
            score += 0.25 * vol_component
            if snapshot.realized_vol_pct >= self._value('shock_realized_vol_reason_floor', 0.90):
                reasons.append('volatility_burst')
        if snapshot.trade_burst_score is not None:
            score += 0.25 * self._clamp(snapshot.trade_burst_score / self._value('shock_trade_burst_scale', 1.0))
            if snapshot.trade_burst_score >= self._value('shock_trade_burst_reason_floor', 0.5):
                reasons.append('trade_burst')
        if snapshot.liquidation_spike_score is not None:
            score += 0.25 * self._clamp(snapshot.liquidation_spike_score / self._value('shock_liquidation_scale', 1.0))
            if snapshot.liquidation_spike_score >= self._value('shock_liquidation_reason_floor', 0.5):
                reasons.append('liquidation_spike')
        if snapshot.orderbook_imbalance is not None:
            imbalance_component = self._clamp((abs(snapshot.orderbook_imbalance) - self._value('shock_imbalance_floor', 0.35)) / self._value('shock_imbalance_window', 0.65))
            score += 0.15 * imbalance_component
            if abs(snapshot.orderbook_imbalance) >= self._value('shock_imbalance_reason_floor', 0.5):
                reasons.append('book_imbalance')
        if snapshot.vwap_deviation_z is not None:
            vwap_component = self._clamp((abs(snapshot.vwap_deviation_z) - self._value('shock_vwap_floor', 0.8)) / self._value('shock_vwap_window', 2.2))
            score += 0.10 * vwap_component
            if abs(snapshot.vwap_deviation_z) >= self._value('shock_vwap_reason_floor', 1.6):
                reasons.append('fast_vwap_dislocation')
        return self._clamp(score), reasons

    def classify(self, snapshot: FeatureSnapshot) -> RegimeDecision:
        shock_score, shock_reasons = self._score_shock(snapshot)
        crowded_score, crowded_reasons = self._score_crowded(snapshot)
        trend_score, trend_reasons = self._score_trend(snapshot)
        range_score, range_reasons = self._score_range(snapshot)
        compression_score, compression_reasons = self._score_compression(snapshot)
        scores = {
            Regime.TREND.value: trend_score,
            Regime.RANGE.value: range_score,
            Regime.COMPRESSION.value: compression_score,
            Regime.CROWDED.value: crowded_score,
            Regime.SHOCK.value: shock_score,
        }
        if shock_score >= self._value('shock_activation_threshold', 0.50):
            return RegimeDecision(primary=Regime.SHOCK, confidence=shock_score, reasons=shock_reasons, scores=scores)
        if crowded_score >= self._value('crowded_activation_threshold', 0.65):
            return RegimeDecision(primary=Regime.CROWDED, confidence=crowded_score, reasons=crowded_reasons, scores=scores)
        ranked = sorted([
            (Regime.TREND, trend_score, trend_reasons),
            (Regime.RANGE, range_score, range_reasons),
            (Regime.COMPRESSION, compression_score, compression_reasons),
        ], key=lambda x: x[1], reverse=True)
        top_regime, top_score, top_reasons = ranked[0]
        second_regime, second_score, _ = ranked[1]
        if top_score < self._value('label_activation_threshold', 0.55):
            return RegimeDecision(primary=Regime.CHAOTIC, confidence=max(0.35, top_score), reasons=['top_score_below_activation_threshold'], secondary=[top_regime, second_regime], scores=scores)
        if (top_score - second_score) < self._value('label_gap_threshold', 0.08):
            return RegimeDecision(primary=Regime.CHAOTIC, confidence=top_score, reasons=['top_scores_too_close'], secondary=[top_regime, second_regime], scores=scores)
        return RegimeDecision(primary=top_regime, confidence=top_score, reasons=top_reasons, secondary=[r[0] for r in ranked[1:]], scores=scores)
