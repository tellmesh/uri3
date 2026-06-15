from .parser import parse_uri


def normalize_uri(uri: str) -> str:
    p = parse_uri(uri.strip())
    scheme = p.scheme.lower()
    if scheme in {"http", "https"}:
        return f"{scheme}://{p.netloc.lower()}{p.path}"
    return f"{scheme}://{p.netloc}{p.path}" if p.netloc else f"{scheme}:{p.path}"
