from __future__ import annotations

from pathlib import Path
from typing import Any

from uri3.doctor.checks._helpers import check_result
from uri3.resolvers.explain import default_touri_registry, load_touri_config


def check_config(root: Path) -> dict[str, Any]:
    touri_cfg_path = root / "config" / "touri.uri.yaml"
    operator_cfg_path = root / "config" / "operator_registry.uri.yaml"
    uri3_cfg_path = root / "config" / "uri3.uri.yaml"
    touri_cfg = load_touri_config(root)
    registry_path = default_touri_registry(root)
    missing = [
        name
        for name, path in (
            ("config/touri.uri.yaml", touri_cfg_path),
            ("config/operator_registry.uri.yaml", operator_cfg_path),
            ("config/uri3.uri.yaml", uri3_cfg_path),
        )
        if not path.is_file()
    ]
    return check_result(
        "config",
        ok=not missing,
        paths={
            "touri": str(touri_cfg_path),
            "operator_registry": str(operator_cfg_path),
            "uri3": str(uri3_cfg_path),
        },
        registry_path=str(registry_path),
        resolution_order=list(touri_cfg.get("resolution_order") or []),
        missing=missing,
    )
