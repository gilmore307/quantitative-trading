from __future__ import annotations

import argparse
import json

from src.config.settings import Settings
from src.runtime.workflows import OkxWorkflowHooks, run_strategy_upgrade_event


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description='Run unified strategy upgrade event workflow for quantitative-trading.')
    parser.add_argument('--destructive', action='store_true', help='Deprecated compatibility flag; ignored by the current upgrade event path.')
    return parser


def main() -> None:
    args = build_arg_parser().parse_args()
    settings = Settings.load()
    settings.ensure_demo_only()
    hooks = OkxWorkflowHooks(settings)
    payload = run_strategy_upgrade_event(hooks=hooks, destructive=args.destructive)
    print(json.dumps(payload, ensure_ascii=False, default=str, indent=2))


if __name__ == '__main__':
    main()
