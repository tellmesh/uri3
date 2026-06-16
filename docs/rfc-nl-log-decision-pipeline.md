# RFC: NL log decision pipeline (`log://` → `llm://` → `if:`)

Status: **draft / MVP implemented in uri3**  
Scope: uri3 workflow executor, urirdp runtime, tellmesh flows

## Problem

Automation needs runtime decisions from log content without splitting inference (`llm://`) from
transport bridges (`chat://`). Today:

- `log://` works in `uri3 logs` CLI but workflow steps were **mock no-ops**
- `chat://local/uri/command/execute` maps phrases — **not** an LLM judge
- `if:` supports `step.field == true|false` and `step.field == "string"`

## Standard pipeline

```txt
log:// (data)  →  llm://…/text/query/decide (NL judge)  →  ok: bool  →  if:  →  action URI
```

| Layer | Scheme | Role |
|-------|--------|------|
| Data | `log://`, `stt://`, `ocr://` | read-only context |
| Reasoning | `llm://…/text/query/decide` | NL judge → `{ok, decision, reason}` |
| Action | `rdp://`, `kvm://`, `hypervisor://` | side effects |
| Notify | `message://` (future) | human escalation without LLM |

## New operation: `llm://{target}/text/query/decide`

### Request payload

```yaml
question: "Czy logi wskazują na problem z forwardem do urirdp?"
context_from: read_logs          # step id → prior step output injected as context
expect: boolean                  # maps verdict → step ok for if:
driver: mock | litellm           # optional; default mock in dry-run
model: openrouter/google/gemini-2.0-flash-001
```

### Response shape

```json
{
  "ok": true,
  "decision": "retry",
  "reason": "3× HTTP 502 in last 5 minutes",
  "confidence": 0.87,
  "model": "mock-decide",
  "question": "…"
}
```

**Branching contract:** `ok: true` means “execute remediation branch”.  
Use `if: nl_decide.ok == true` / `if: nl_decide.ok == false`.

## `context_from` resolution

Workflow adapters resolve these keys before execution:

| Key | Injects as |
|-----|------------|
| `context_from` | `context` |
| `transcript_from` | `transcript` |
| `actual_from` | `actual` |

Implementation: `uri3/graph/payload_context.py`

## chat:// deprecation path

| Today | Target |
|-------|--------|
| `chat://local/uri/command/execute` (phrase map) | `llm://…/text/query/plan` + forward |
| `chat://local/message/command/send` | `message://…/alert/command/send` |
| `chat://tellmesh/prompt` (urish) | unchanged — UI ask encoding |

Do **not** rename `chat://tellmesh/prompt`. Lab voice bridge may remain as shim.

## Implementation status

| Component | Status |
|-----------|--------|
| `LogAdapter` (uri3 graph) | ✅ MVP |
| `LlmAdapter` decide (uri3 graph) | ✅ MVP mock + litellm optional |
| `urirdp_llm.handlers.decide` | ✅ MVP |
| `flow_defaults.uri.yaml` decide match | ✅ |
| Lab `log://` forward | ✅ local via LogAdapter in LabCallAdapter |
| `message://` notify scheme | ✅ lab + uri3 MessageAdapter |
| Flow 08 STT→llm plan→kvm | ✅ updated |
| `if: step.decision == "retry"` | ✅ string compare |

## Example flow

See `examples/nl-log-decision.uri.flow.yaml`.

## References

- `uri3/graph/adapters/log_adapter.py`
- `uri3/graph/adapters/llm_adapter.py`
- `uri3/llm/decide.py`
- `urisys/urirdp-docker/packages/python/urirdp_llm/handlers.py`
- `tellmesh/examples/15_compact_uri_flow/branching.uri.flow.yaml`
