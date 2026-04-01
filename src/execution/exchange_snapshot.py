from __future__ import annotations

from dataclasses import dataclass

from src.config.settings import Settings
from src.exchange.okx_client import OkxClient, live_position_snapshot
from src.reconcile.alignment import ExchangePositionSnapshot


@dataclass(slots=True)
class ExchangeSnapshotProvider:
    settings: Settings

    def fetch_position(self, account: str, symbol: str) -> ExchangePositionSnapshot | None:
        okx = OkxClient(self.settings, self.settings.active_live_account())
        execution_symbol = self.settings.execution_symbol(strategy_name, symbol)
        snap = live_position_snapshot(okx.exchange, execution_symbol)
        if snap is None:
            return None
        return ExchangePositionSnapshot(
            account=account,
            symbol=symbol,
            side=snap.get('side'),
            size=float(snap.get('contracts') or 0.0),
        )
