from uri3.protocols.parser import parse_uri
from uri3.protocols.schemes import SUPPORTED_SCHEMES


def validate_uri(uri: str) -> bool:
    parsed = parse_uri(uri)
    if parsed.scheme not in SUPPORTED_SCHEMES:
        raise ValueError(f"Unsupported URI scheme: {parsed.scheme}")
    return True
