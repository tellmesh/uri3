# uri3


## AI Cost Tracking

![PyPI](https://img.shields.io/badge/pypi-costs-blue) ![Version](https://img.shields.io/badge/version-0.5.8-blue) ![Python](https://img.shields.io/badge/python-3.9+-blue) ![License](https://img.shields.io/badge/license-Apache--2.0-green)
![AI Cost](https://img.shields.io/badge/AI%20Cost-$0.50-orange) ![Human Time](https://img.shields.io/badge/Human%20Time-3.0h-blue) ![Model](https://img.shields.io/badge/Model-openrouter%2Fqwen%2Fqwen3--coder--next-lightgrey)

- 🤖 **LLM usage:** $0.5038 (7 commits)
- 👤 **Human dev:** ~$296 (3.0h @ $100/h, 30min dedup)

Generated on 2026-06-15 using [openrouter/qwen/qwen3-coder-next](https://openrouter.ai/qwen/qwen3-coder-next)

---

TellMesh URI package extracted from [tellmesh/tellmesh](https://github.com/tellmesh/tellmesh).

**Role:** URI discovery, resolution, validation, workflow graphs, and routing.

```text
nl2uri    -> natural language -> URI tree / flow / graph
uri2flow  -> compact URI flow -> expanded workflow graph
uri3      -> resolve, validate, plan, dry-run, run workflows
uri2ops   -> operator execution (browser, screen, robot, …)
touri     -> capability manifests -> uri2run backends
hypervisor -> deployment registry, policy, lifecycle
```

## Install

```bash
pip install -e .
# or from monorepo umbrella:
cd ../tellmesh && uv sync
```

## CLI quickstart

```bash
uri3                          # quick reference
uri3 resolve http://localhost:8101/health
uri3 explain weather://forecast/Gdansk/14/html
uri3 validate-workflow examples/14_workflow_executor_mock/workflow.mock.yaml
uri3 plan-workflow examples/14_workflow_executor_mock/workflow.mock.yaml
uri3 run-workflow examples/14_workflow_executor_mock/workflow.mock.yaml --dry-run
uri3 expand-flow examples/15_compact_uri_flow/weather.uri.flow.yaml
uri3 doctor
uri3 replay check-agent-health
```

## Examples

| Example | Path |
|---------|------|
| HTTP scan | [`tellmesh/examples/02_uri3_scan_http`](../tellmesh/examples/02_uri3_scan_http) |
| Workflow mock | [`tellmesh/examples/14_workflow_executor_mock`](../tellmesh/examples/14_workflow_executor_mock) |
| Compact flow | [`tellmesh/examples/15_compact_uri_flow`](../tellmesh/examples/15_compact_uri_flow) |

Run all from monorepo: `bash tellmesh/examples/run_all.sh`

## Links

- [TODO](TODO.md) · [CHANGELOG](CHANGELOG.md)
- [uri2flow](../uri2flow) · [uri2ops](../uri2ops) · [nl2uri](../nl2uri)
- Org status: [`../TODO_STATUS.md`](../TODO_STATUS.md)


## License

Licensed under Apache-2.0.
