from __future__ import annotations

import argparse
import json
import sys

from ai_agent.agent import ToolCallingAgent
from ai_agent.logging_config import setup_logging


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run a small tool-calling agent prototype.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    run_parser = subparsers.add_parser("run", help="Run the agent on one prompt")
    run_parser.add_argument("prompt", help="Prompt for the agent")
    run_parser.add_argument("--log-file", default="logs/agent.log", help="Log file path")

    return parser.parse_args()


def main() -> int:
    args = parse_args()
    setup_logging(args.log_file)

    if args.command == "run":
        output = ToolCallingAgent().run(args.prompt)
        print(json.dumps(output, indent=2))
        return 0 if output["success"] or output["safety"]["blocked"] else 1

    print("Unknown command", file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
