from __future__ import annotations

from pathlib import Path

from uri3.resolvers.file_resolver import path_from_file_uri, resolve_file


def test_resolve_file_uri_returns_metadata(tmp_path: Path):
    source = tmp_path / "source.md"
    source.write_text("# Source\n", encoding="utf-8")

    result = resolve_file(f"file://{source.as_posix()}")

    assert result["scheme"] == "file"
    assert result["exists"] is True
    assert result["is_file"] is True
    assert result["resolved_path"] == str(source.resolve())
    assert result["mime_type"] == "text/markdown"
    assert result["content"] == "# Source\n"
    assert result["content_truncated"] is False


def test_path_from_file_uri_unquotes_spaces(tmp_path: Path):
    path = tmp_path / "source file.md"

    result = path_from_file_uri(f"file://{str(path).replace(' ', '%20')}")

    assert result == path
