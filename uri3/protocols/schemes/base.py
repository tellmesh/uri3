from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class QueryOption:
    name: str
    type: str
    aliases: tuple[str, ...] = ()
    default: Any = None
    enum: tuple[str, ...] | None = None
    description: str = ""

    def to_dict(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "name": self.name,
            "type": self.type,
            "description": self.description,
        }
        if self.aliases:
            payload["aliases"] = list(self.aliases)
        if self.default is not None:
            payload["default"] = self.default
        if self.enum:
            payload["enum"] = list(self.enum)
        return payload


@dataclass(frozen=True)
class SchemeSpec:
    scheme: str
    description: str
    template: str
    netloc: dict[str, Any] = field(default_factory=dict)
    path: dict[str, Any] = field(default_factory=dict)
    query: tuple[QueryOption, ...] = ()
    constants: dict[str, Any] = field(default_factory=dict)
    actions: tuple[str, ...] = ("resolve",)
    cli: tuple[str, ...] = ()
    python_api: tuple[str, ...] = ()
    examples: tuple[str, ...] = ()
    documented: bool = True

    def to_dict(self) -> dict[str, Any]:
        from uri3.protocols.schemes.constants import SUPPORTED_SCHEMES

        return {
            "scheme": self.scheme,
            "supported": self.scheme in SUPPORTED_SCHEMES,
            "documented": self.documented,
            "description": self.description,
            "template": self.template,
            "format": {
                "netloc": self.netloc,
                "path": self.path,
                "query": [option.to_dict() for option in self.query],
            },
            "constants": self.constants,
            "actions": list(self.actions),
            "api": {
                "cli": list(self.cli),
                "python": list(self.python_api),
            },
            "examples": list(self.examples),
        }
