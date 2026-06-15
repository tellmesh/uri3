from uri3.protocols.schemes.base import QueryOption, SchemeSpec


def spec() -> SchemeSpec:
    from uri3.logs.reader import DEFAULT_STREAM_FILES
    from uri3.resolvers.log_resolver import LOG_LEVELS

    return SchemeSpec(
        scheme="log",
        description="Read and filter repository log files by stream, path, and query filters.",
        template="log://{stream}[/{path}][?{query}]",
        netloc={
            "name": "stream",
            "required": False,
            "default": "hypervisor",
            "description": "Named log stream or the special value `file` for explicit paths.",
            "known_values": {
                key: value for key, value in DEFAULT_STREAM_FILES.items() if key != "default"
            },
        },
        path={
            "required": False,
            "description": "Optional repo-relative log path. Required when stream=file.",
        },
        query=(
            QueryOption(
                "level",
                "enum",
                aliases=("min_level",),
                enum=LOG_LEVELS,
                description="Minimum log level to include.",
            ),
            QueryOption("grep", "string", aliases=("q", "contain"), description="Case-insensitive substring filter."),
            QueryOption("logger", "string", aliases=("component",), description="Filter by logger/component name."),
            QueryOption(
                "since",
                "string",
                aliases=("from",),
                description="Lower time bound: ISO timestamp or relative duration (1h, 30m, 2d).",
            ),
            QueryOption(
                "until",
                "string",
                aliases=("to",),
                description="Upper time bound: ISO timestamp or relative duration.",
            ),
            QueryOption("limit", "integer", default=100, description="Maximum number of entries to return."),
            QueryOption("offset", "integer", default=0, description="Skip this many matched entries."),
            QueryOption(
                "tail",
                "boolean",
                default=False,
                description="When true with limit, return the last N matched entries.",
            ),
            QueryOption(
                "format",
                "string",
                default="auto",
                description="Log line format hint: auto, json, or text.",
            ),
        ),
        constants={"levels": list(LOG_LEVELS), "streams": dict(DEFAULT_STREAM_FILES)},
        actions=("resolve", "read", "summarize", "scan", "call"),
        cli=("uri3 logs", "uri3 scan", "uri3 resolve", "uri3 schema"),
        python_api=(
            "uri3.logs.reader.read_logs",
            "uri3.logs.reader.summarize_logs",
            "uri3.resolvers.log_resolver.parse_log_uri",
            "uri3.resolvers.router.call",
        ),
        examples=(
            "log://hypervisor?level=ERROR&grep=deployment&limit=20",
            "log://hypervisor?since=1h&tail=1&limit=50",
            "log://file/output/logs/hypervisor.log?grep=timeout",
        ),
    )
