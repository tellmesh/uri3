from dataclasses import dataclass
from urllib.parse import urlparse, parse_qs

@dataclass(frozen=True)
class ParsedURI:
    raw: str
    scheme: str
    netloc: str
    path: str
    query: dict


def parse_uri(uri: str) -> ParsedURI:
    parsed = urlparse(uri)
    if not parsed.scheme:
        raise ValueError(f"URI has no scheme: {uri}")
    return ParsedURI(uri, parsed.scheme, parsed.netloc, parsed.path, parse_qs(parsed.query))
