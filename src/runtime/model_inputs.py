from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from src.upgrade.strategy_pointer import ActiveStrategySnapshot


DEFAULT_MODEL_INPUTS_PATH = Path('/root/.openclaw/workspace/projects/quantitative-trading/logs/runtime/active-model-inputs.json')


def load_model_inputs(active_strategy: ActiveStrategySnapshot | None = None, path: str | Path | None = None) -> dict[str, Any]:
    candidate = Path(path) if path is not None else None
    paths = [p for p in [candidate, DEFAULT_MODEL_INPUTS_PATH] if p is not None]
    for p in paths:
        if p.exists():
            payload = json.loads(p.read_text(encoding='utf-8'))
            if not isinstance(payload, dict):
                raise RuntimeError('invalid_model_inputs_payload')
            return payload
    raise RuntimeError('missing_model_inputs')
