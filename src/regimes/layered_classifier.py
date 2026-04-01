from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from src.features.engine import FeatureEngine
from src.features.models import FeatureSnapshot
from src.market.models import MarketSnapshot
from src.regimes.classifier import RuleBasedRegimeClassifier
from src.regimes.models import Regime, RegimeDecision


@dataclass(slots=True)
class LayeredRegimeDecision:
    background_4h: RegimeDecision
    primary_15m: RegimeDecision
    override_1m: RegimeDecision | None
    final: RegimeDecision
    background_features: FeatureSnapshot
    primary_features: FeatureSnapshot
    override_features: FeatureSnapshot


class LayeredRegimeClassifier:
    """Three-layer label calculator driven by external parameters.

    Runtime still calculates labels locally, but the calculation thresholds and
    overrides should come from external model inputs rather than being locked to
    static runtime constants.
    """

    def __init__(self, parameters: dict[str, Any] | None = None):
        self.parameters = parameters or {}
        self.background_engine = FeatureEngine(trend_timeframe='4h', range_timeframe='4h', event_timeframe='1m', layer_name='background_4h')
        self.primary_engine = FeatureEngine(trend_timeframe='15m', range_timeframe='15m', event_timeframe='1m', layer_name='primary_15m')
        self.override_engine = FeatureEngine(trend_timeframe='15m', range_timeframe='15m', event_timeframe='1m', layer_name='event_1m')
        self.classifier = RuleBasedRegimeClassifier(parameters=self.parameters)

    def _value(self, key: str, default: float) -> float:
        value = self.parameters.get(key, default)
        try:
            return float(value)
        except (TypeError, ValueError):
            return float(default)

    def classify(self, snapshot: MarketSnapshot) -> LayeredRegimeDecision:
        bg_features = self.background_engine.build(snapshot)
        primary_features = self.primary_engine.build(snapshot)
        override_features = self.override_engine.build(snapshot)

        background = self.classifier.classify(bg_features)
        primary = self.classifier.classify(primary_features)
        override_candidate = self.classifier.classify(override_features)

        shock_label = str(self.parameters.get('override_shock_label', Regime.SHOCK.value))
        override = override_candidate if override_candidate.primary.value == shock_label else None
        final = primary

        if override is not None:
            final = RegimeDecision(
                primary=Regime.SHOCK,
                confidence=max(primary.confidence, override.confidence),
                reasons=['1m_event_override', *override.reasons],
                secondary=[primary.primary, *override.secondary],
            )
        elif background.primary == Regime.TREND and primary.primary == Regime.RANGE and background.confidence >= self._value('background_override_min_confidence', 0.65):
            final = RegimeDecision(
                primary=Regime.TREND,
                confidence=min(0.95, max(primary.confidence, background.confidence)),
                reasons=['4h_trend_background_override', *background.reasons, *primary.reasons],
                secondary=[Regime.RANGE, *primary.secondary],
            )

        return LayeredRegimeDecision(
            background_4h=background,
            primary_15m=primary,
            override_1m=override,
            final=final,
            background_features=bg_features,
            primary_features=primary_features,
            override_features=override_features,
        )
