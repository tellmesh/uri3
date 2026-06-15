from dataclasses import dataclass
@dataclass
class ScanItem:
    uri: str
    kind: str
    status: str
    metadata: dict
