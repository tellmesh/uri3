from uri3.protocols.schemes.base import QueryOption, SchemeSpec


def spec() -> SchemeSpec:
    return SchemeSpec(
        scheme="docker",
        description="Control Docker Compose stacks, containers, and generated agent deployments.",
        template="docker://{kind}/{target}[?{query}]",
        netloc={
            "name": "kind",
            "required": True,
            "description": "Target kind: stack, compose, container, agent, generate.",
            "enum": ["stack", "compose", "container", "agent", "generate"],
        },
        path={"name": "target", "required": True, "description": "Stack id, compose path, container name, or agent id."},
        query=(
            QueryOption(
                "action",
                "enum",
                enum=("status", "ps", "inspect", "up", "down", "start", "stop", "restart", "logs", "generate"),
                default="status",
                description="Docker control action.",
            ),
            QueryOption("dry_run", "boolean", default=False, description="Return command plan without executing."),
            QueryOption("build", "boolean", default=True, description="Build images on compose up."),
            QueryOption("detach", "boolean", default=True, description="Run compose up in detached mode."),
            QueryOption("remove_volumes", "boolean", default=False, description="Remove volumes on compose down."),
            QueryOption("tail", "integer", default=100, description="Tail length for logs action."),
        ),
        actions=("resolve", "scan", "call"),
        cli=("uri3 scan", "uri3 resolve", "uri3 call", "uri3 schema"),
        python_api=(
            "uri3.resolvers.docker_resolver.resolve_docker",
            "uri3.docker.controller.control_docker",
            "uri3.scanner.docker_scanner.scan_docker",
        ),
        examples=(
            "docker://stack/ssh-testenv?action=up",
            "docker://stack/ssh-testenv?action=down&remove_volumes=1",
            "docker://container/hypervisor-ssh-agent-host?action=stop",
            "docker://generate/weather-map-agent?action=generate",
        ),
    )
