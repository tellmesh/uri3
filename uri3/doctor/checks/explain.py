from __future__ import annotations

from pathlib import Path
from typing import Any

from uri3.doctor.checks._helpers import check_result
from uri3.resolvers.explain import explain_uri


def check_explain_smoke(root: Path, registry_path: Path) -> dict[str, Any]:
    from touri.loader import load_registry
    from touri.register import sample_uri_from_template

    if not registry_path.exists():
        return check_result(
            "explain.smoke", ok=False, mismatches=[], errors=["registry path missing"]
        )

    manifests = load_registry(registry_path)
    mismatches: list[dict[str, str]] = []
    for manifest in manifests:
        sample_uri = sample_uri_from_template(manifest.capability.uri_template)
        explain = explain_uri(sample_uri, registry_root=registry_path, root=root)
        matched = explain.get("matched_registry")
        if matched != "touri":
            mismatches.append(
                {
                    "capability": manifest.capability.id,
                    "sample_uri": sample_uri,
                    "matched_registry": str(matched),
                }
            )
    return check_result(
        "explain.smoke",
        ok=not mismatches,
        checked=len(manifests),
        mismatches=mismatches,
    )
