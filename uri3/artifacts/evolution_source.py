from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class EvolutionSource:
    uri: str
    kind: str
    schema: str | None = None

    def to_dict(self) -> dict[str, Any]:
        payload: dict[str, Any] = {"uri": self.uri, "kind": self.kind}
        if self.schema:
            payload["schema"] = self.schema
        return payload


_SOURCE_KIND_BY_SCHEME = {
    "incident": ("Incident", "schemas/incident.schema.json"),
    "ticket": ("Ticket", "schemas/ticket.schema.json"),
    "diagnosis": ("Diagnosis", "schemas/diagnosis.schema.json"),
    "test": ("RegressionTest", "schemas/regression_test.schema.json"),
    "strategy": ("Strategy", None),
    "manual": ("ManualRequest", None),
}


def _scheme_from_uri(uri: str) -> str:
    if "://" not in uri:
        return ""
    return uri.split("://", 1)[0]


def normalize_evolution_source(
    *,
    uri: str,
    kind: str | None = None,
    schema: str | None = None,
) -> EvolutionSource:
    scheme = _scheme_from_uri(uri)
    default_kind, default_schema = _SOURCE_KIND_BY_SCHEME.get(scheme, ("Unknown", None))
    return EvolutionSource(
        uri=uri,
        kind=kind or default_kind,
        schema=schema or default_schema,
    )


def evolution_proposal_uri(source: EvolutionSource) -> str:
    scheme = _scheme_from_uri(source.uri)
    if scheme == "incident":
        incident_id = source.uri.rsplit("/", 1)[-1]
        return f"evolution://proposal/from-incident/{incident_id}"
    if scheme == "ticket":
        ticket_id = source.uri.rsplit("/", 1)[-1]
        return f"evolution://proposal/from-ticket/{ticket_id}"
    if scheme == "diagnosis":
        diagnosis_id = source.uri.rsplit("/", 1)[-1]
        return f"evolution://proposal/from-diagnosis/{diagnosis_id}"
    if scheme == "test":
        test_id = source.uri.rsplit("/", 1)[-1]
        return f"evolution://proposal/from-test-failure/{test_id}"
    slug = source.uri.replace("://", "/").replace("/", "_")
    return f"evolution://proposal/from-source/{slug}"


def attach_evolution_source(payload: dict[str, Any], source: EvolutionSource) -> dict[str, Any]:
    body = dict(payload)
    body["source"] = source.to_dict()
    body.setdefault("uri", {})
    if isinstance(body["uri"], dict):
        body["uri"]["source"] = source.uri
        body["uri"].setdefault("self", evolution_proposal_uri(source))
    return body
