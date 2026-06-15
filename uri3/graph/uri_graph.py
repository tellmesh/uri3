from dataclasses import dataclass, field
from pathlib import Path
import yaml

@dataclass
class UriNode:
    uri: str
    kind: str
    name: str | None = None

@dataclass
class UriEdge:
    source: str
    target: str
    relation: str

@dataclass
class UriGraph:
    nodes: dict[str, UriNode] = field(default_factory=dict)
    edges: list[UriEdge] = field(default_factory=list)
    def add_node(self, uri, kind, name=None):
        if uri and uri not in self.nodes:
            self.nodes[uri] = UriNode(uri, kind, name)
    def add_edge(self, source, target, relation):
        if source and target:
            self.edges.append(UriEdge(source, target, relation))


def build_graph_from_tree(path) -> UriGraph:
    data = yaml.safe_load(Path(path).read_text(encoding="utf-8"))
    g = UriGraph()
    domain_uri = data.get("domain", {}).get("uri")
    g.add_node(domain_uri, "domain", data.get("domain", {}).get("id"))
    for group, kind in [("inputs","input"),("commands","command"),("events","event"),("resources","resource"),("artifacts","artifact")]:
        for name, item in (data.get(group) or {}).items():
            uri = item.get("uri") or item.get("uri_template")
            if uri:
                g.add_node(uri, kind, name)
                g.add_edge(domain_uri, uri, f"has_{kind}")
            for key in ["handler_uri", "public_url_template", "api_key_uri"]:
                if item.get(key):
                    g.add_node(item[key], key.replace("_uri", ""), key)
                    g.add_edge(uri, item[key], key)
    agent = data.get("agent", {})
    if agent.get("uri"):
        g.add_node(agent["uri"], "agent", agent.get("id"))
        g.add_edge(domain_uri, agent["uri"], "exposed_by")
    if agent.get("card_uri"):
        g.add_node(agent["card_uri"], "agent_card", "card")
        g.add_edge(agent.get("uri"), agent["card_uri"], "has_card")
    return g
