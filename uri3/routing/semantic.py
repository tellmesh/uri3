from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, urlparse

from uri3.protocols.normalizer import normalize_uri


class UriKind(str, Enum):
    command = "command"
    query = "query"
    resource = "resource"
    event = "event"
    view = "view"
    health = "health"
    repair = "repair"


@dataclass(frozen=True)
class UriRoute:
    input_uri: str
    canonical_uri: str
    namespace: str
    domain: str
    kind: UriKind
    action: str | None = None
    scheme: str | None = None
    resource_path: tuple[str, ...] = ()
    query: dict[str, str] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["kind"] = self.kind.value
        payload["resource_path"] = list(self.resource_path)
        return payload


@dataclass(frozen=True)
class SemanticRouteResolution:
    route: UriRoute
    contract_uri: str | None = None
    policy_uri: str | None = None
    matched_registry: str | None = None
    side_effects: bool = False
    requires_approval: bool = False
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            **self.route.to_dict(),
            "contract_uri": self.contract_uri,
            "policy_uri": self.policy_uri,
            "matched_registry": self.matched_registry,
            "side_effects": self.side_effects,
            "requires_approval": self.requires_approval,
            "metadata": dict(self.metadata),
        }


_OPERATOR_SCHEMES = frozenset(
    {"browser", "dom", "screen", "input", "android", "pcwin", "robot", "device"}
)
_COMMAND_NAMES = frozenset(
    {"open", "click", "type", "tap", "focus", "move", "stop", "mission_start", "write"}
)


def normalize_route(uri: str, *, root: str | Path | None = None) -> UriRoute:
    """Return a semantic route without selecting an agent or executing anything."""
    parsed = urlparse(uri.strip())
    if not parsed.scheme:
        raise ValueError(f"URI has no scheme: {uri}")
    if parsed.scheme == "tellmesh":
        return _route_from_tellmesh_uri(uri)
    if parsed.scheme in _OPERATOR_SCHEMES:
        return _route_from_operator_uri(uri, root=root)
    return _route_from_generic_uri(uri)


def explain_semantic_uri(
    uri: str,
    *,
    root: str | Path | None = None,
) -> SemanticRouteResolution:
    route = normalize_route(uri, root=root)
    spec = _operation_spec(route, root=root)
    contract_uri = _contract_uri(spec)
    side_effects = (
        bool(getattr(spec, "side_effects", False))
        if spec
        else _side_effect_default(route)
    )
    requires_approval = bool(getattr(spec, "requires_policy", False)) if spec else side_effects
    policy_uri = (
        f"policy://{route.domain}/{route.action}"
        if route.action and (requires_approval or route.kind == UriKind.command)
        else None
    )
    matched_registry = "uri2ops" if route.scheme in _OPERATOR_SCHEMES else None
    metadata: dict[str, Any] = {}
    if spec is not None:
        metadata["operation"] = spec.to_dict()
    return SemanticRouteResolution(
        route=route,
        contract_uri=contract_uri,
        policy_uri=policy_uri,
        matched_registry=matched_registry,
        side_effects=side_effects,
        requires_approval=requires_approval,
        metadata=metadata,
    )


def _route_from_tellmesh_uri(uri: str) -> UriRoute:
    parsed = urlparse(uri)
    parts = _uri_parts(parsed)
    namespace = "tellmesh"
    domain_parts = parts[:2] if parts and parts[0] == "operators" else parts[:1]
    if parts and parts[0] == "operators":
        kind_value = parts[2] if len(parts) >= 3 else "resource"
        action = parts[3] if len(parts) >= 4 else None
    else:
        kind_value = parts[1] if len(parts) >= 2 else "resource"
        action = parts[2] if len(parts) >= 3 else None
    kind = _kind_from_value(kind_value)
    scheme = domain_parts[-1] if domain_parts else None
    return UriRoute(
        input_uri=uri,
        canonical_uri=uri,
        namespace=namespace,
        domain="/".join(domain_parts) if domain_parts else namespace,
        kind=kind,
        action=action,
        scheme=scheme,
        resource_path=tuple(parts[4:] if parts and parts[0] == "operators" else parts[3:]),
        query=_flat_query(parsed),
    )


def _route_from_operator_uri(uri: str, *, root: str | Path | None = None) -> UriRoute:
    parsed = urlparse(uri)
    input_scheme = parsed.scheme.lower()
    parts = _uri_parts(parsed)
    action = _operator_action(input_scheme, parts)
    canonical_scheme = _registry_scheme(input_scheme)
    spec = _operation_spec_for(canonical_scheme, action, root=root)
    kind = _kind_from_value(getattr(spec, "kind", None) or _default_kind(action))
    canonical_uri = f"tellmesh://operators/{canonical_scheme}/{kind.value}/{action}"
    return UriRoute(
        input_uri=uri,
        canonical_uri=canonical_uri,
        namespace="tellmesh",
        domain=f"operators/{canonical_scheme}",
        kind=kind,
        action=action,
        scheme=input_scheme,
        resource_path=tuple(parts[:-1]),
        query=_flat_query(parsed),
    )


def _route_from_generic_uri(uri: str) -> UriRoute:
    parsed = urlparse(uri)
    scheme = parsed.scheme.lower()
    kind = _kind_from_value(scheme if scheme in UriKind._value2member_map_ else "resource")
    canonical_uri = normalize_uri(uri)
    return UriRoute(
        input_uri=uri,
        canonical_uri=canonical_uri,
        namespace=scheme,
        domain=scheme,
        kind=kind,
        action=_uri_parts(parsed)[-1] if _uri_parts(parsed) else None,
        scheme=scheme,
        resource_path=tuple(_uri_parts(parsed)),
        query=_flat_query(parsed),
    )


def _operation_spec(route: UriRoute, *, root: str | Path | None = None) -> Any | None:
    if not route.scheme or not route.action:
        return None
    return _operation_spec_for(_registry_scheme(route.scheme), route.action, root=root)


def _operation_spec_for(
    scheme: str,
    operation: str,
    *,
    root: str | Path | None = None,
) -> Any | None:
    try:
        from uri2ops.remote_registry.loader import resolve_operation_registry

        registry = resolve_operation_registry(root=Path(root) if root else None)
        return registry.get(scheme, operation)
    except Exception:
        return None


def _registry_scheme(scheme: str) -> str:
    try:
        from uri2ops.operation_registry.uri_mapping import registry_scheme

        return registry_scheme(scheme)
    except Exception:
        return "browser" if scheme == "dom" else scheme


def _registry_operation(scheme: str, operation: str) -> str:
    try:
        from uri2ops.operation_registry.uri_mapping import registry_operation

        return registry_operation(scheme, operation)
    except Exception:
        return operation


def _operator_action(scheme: str, parts: list[str]) -> str:
    if scheme == "dom":
        return "extract_dom"
    raw = parts[-1] if parts else "call"
    return _registry_operation(scheme, raw)


def _uri_parts(parsed) -> list[str]:
    parts = [part for part in parsed.path.split("/") if part]
    if parsed.netloc:
        return [parsed.netloc, *parts]
    return parts


def _flat_query(parsed) -> dict[str, str]:
    values = parse_qs(parsed.query, keep_blank_values=True)
    return {key: items[-1] if items else "" for key, items in values.items()}


def _kind_from_value(value: str | None) -> UriKind:
    if value in UriKind._value2member_map_:
        return UriKind(str(value))
    return UriKind.resource


def _default_kind(action: str | None) -> str:
    return "command" if action in _COMMAND_NAMES else "query"


def _side_effect_default(route: UriRoute) -> bool:
    return route.kind == UriKind.command or bool(route.action in _COMMAND_NAMES)


def _contract_uri(spec: Any | None) -> str | None:
    if spec is None:
        return None
    schema = getattr(spec, "input_schema", None) or getattr(spec, "output_schema", None)
    if not schema:
        return None
    return f"contract://{str(schema).replace('.', '/')}"
