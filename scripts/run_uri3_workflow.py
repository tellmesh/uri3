#!/usr/bin/env python3
"""Run a uri3 workflow graph with the current Python interpreter."""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

_SCRIPT_DIR = Path(__file__).resolve().parent
_URI3_ROOT = _SCRIPT_DIR.parent
if str(_URI3_ROOT) not in sys.path:
    sys.path.insert(0, str(_URI3_ROOT))


def _hypervisor_root() -> Path:
    env = os.environ.get("HYPERVISOR_REPO_ROOT")
    if env:
        return Path(env).expanduser().resolve()
    return _SCRIPT_DIR.parents[2].parent / "wronai" / "hypervisor"


ROOT = _hypervisor_root()
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from uri3.graph import (  # noqa: E402
    build_execution_plan,
    dry_run_workflow,
    load_workflow_graph,
    run_workflow,
    validate_workflow_graph,
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("path", help="Workflow graph YAML")
    parser.add_argument("--approve", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--browser", default="auto")
    args = parser.parse_args(argv)

    errors = validate_workflow_graph(args.path)
    if errors:
        print(json.dumps({"ok": False, "errors": errors}, indent=2), file=sys.stderr)
        return 1

    graph = load_workflow_graph(args.path)
    if args.dry_run:
        payload = {
            "phase": "dry_run",
            "plan": build_execution_plan(graph),
            "simulation": dry_run_workflow(graph),
        }
        print(json.dumps(payload, indent=2, ensure_ascii=False))
        return 0

    result = run_workflow(
        graph,
        approve=args.approve,
        dry_run=False,
        browser_mode=args.browser,
    )
    print(json.dumps(result.to_dict(), indent=2, ensure_ascii=False))
    return 0 if result.ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
