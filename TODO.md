# TODO — uri3

**Version:** 0.5.8 · **Role:** URI resolve, scan, validate, workflow graph execution

> Utworzono: 2026-06-16 (wcześniej brak pliku)

## Zrobione

- [x] Scheme resolvers (http, env, llm, docker, …)
- [x] Workflow graph validate / plan / dry-run / run
- [x] `expand-flow` / `run-flow` wrapper na uri2flow
- [x] Operation registry summary dla nl2uri graph planner
- [x] LLM profiles (`config/llm.uri.yaml`)

## Otwarte

- [ ] Ujednolicić operation registry z uri2ops (single source of truth)
- [x] Dokumentacja README poza badge/costs (quickstart CLI)
- [ ] Replay / audit trail dla workflow (cross-package z uri2verify)

## Cross-package

| Funkcja | Paczka |
|---------|--------|
| Compact flow compile | uri2flow |
| Operator steps | uri2ops |
| Capability manifests | touri |
