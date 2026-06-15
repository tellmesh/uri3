from __future__ import annotations

from typing import Any

from uri3.config.cli_shortcuts import cli_examples, scan_shortcuts
from uri3.protocols.scheme_registry import list_schemes


def quick_reference() -> str:
    shortcuts = scan_shortcuts()
    scan_lines = "\n".join(f"  {name:<8} {uri}" for name, uri in shortcuts.items()) or "  (none — edit config/uri3.uri.yaml)"
    examples = cli_examples() or [
        "uri3 list",
        "uri3 scan http",
        "uri3 scan --all",
        "uri3 schema ssh://",
    ]
    example_lines = "\n".join(f"  {line}" for line in examples)
    return f"""uri3 — quick reference

Discovery:
  uri3 list              schemes, shortcuts, examples
  uri3 schema --list     URI schemes (same as: uri3 list --schemes)

Scan (use a name or full URI):
{scan_lines}

  uri3 scan http         scan shortcut by name
  uri3 scan <uri>        scan full URI
  uri3 scan --all        run every configured scan shortcut

Actions:
  uri3 resolve <uri>     resolve URI to structured payload
  uri3 call <uri>        execute docker://, python://, log:// actions
  uri3 validate <uri>    validate URI syntax
  uri3 logs 'log://...'  read filtered logs

Examples:
{example_lines}
"""


def list_payload(*, schemes_only: bool = False) -> dict[str, Any]:
    payload: dict[str, Any] = {"schemes": list_schemes()}
    if schemes_only:
        return payload
    payload["shortcuts"] = {"scan": scan_shortcuts()}
    payload["examples"] = cli_examples()
    payload["commands"] = [
        {"name": "list", "summary": "Show schemes, scan shortcuts, and examples"},
        {"name": "scan", "summary": "Probe http/ssh/docker; use shortcut name or full URI"},
        {"name": "schema", "summary": "Describe a scheme or URI (alias: uri3 list --schemes)"},
        {"name": "resolve", "summary": "Resolve URI to structured payload"},
        {"name": "explain", "summary": "Show registry match and execution path for a URI"},
        {"name": "doctor", "summary": "Validate config, registries, and envelope consistency"},
        {"name": "call", "summary": "Execute callable URI actions"},
        {"name": "validate", "summary": "Validate URI syntax"},
        {"name": "logs", "summary": "Read filtered logs via log:// URI"},
        {"name": "graph", "summary": "Build dependency graph from URI tree YAML"},
        {"name": "expand-flow", "summary": "Expand compact URI flow to workflow graph (uri2flow)"},
        {"name": "run-flow", "summary": "Expand flow and validate/plan/run workflow"},
        {"name": "validate-workflow", "summary": "Validate task/workflow graph YAML"},
        {"name": "plan-workflow", "summary": "Topological execution plan for workflow graph"},
        {"name": "run-workflow", "summary": "Execute workflow (mock adapters); command nodes need --approve"},
        {"name": "replay", "summary": "Summarize workflow JSONL event log for debugging"},
    ]
    return payload
