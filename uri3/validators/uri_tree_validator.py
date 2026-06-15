from pathlib import Path
import json, yaml
from jsonschema import Draft202012Validator

from uri3.paths import find_repo_root

SCHEMA_PATH = find_repo_root(Path(__file__)) / "schemas" / "uri_tree.schema.json"


def load_yaml(path):
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def validate_uri_tree(path) -> list[str]:
    data = load_yaml(path)
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    validator = Draft202012Validator(schema)
    errors = sorted(validator.iter_errors(data), key=lambda e: e.path)
    return [f"{list(e.path)}: {e.message}" for e in errors]
