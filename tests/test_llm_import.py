"""Public LLM entry points must work before graph initialization."""

import os
from pathlib import Path
import subprocess
import sys

import pytest


@pytest.mark.parametrize(
    "script",
    [
        "from uri3.llm.plan import plan; "
        "r = plan(transcript='status rdp'); "
        "assert r['ok'] and r['uri'] == 'rdp://local/display/query/status'",
        "from uri3.llm.decide import decide; "
        "r = decide(question='retry?', context_value={'entries': "
        "[{'level': 'ERROR', 'message': 'HTTP 502'}]}, driver='mock'); "
        "assert r['ok'] and r['decision'] == 'retry'",
    ],
)
def test_llm_entry_point_in_fresh_process(script, tmp_path):
    root = Path(__file__).resolve().parents[1]
    env = {**os.environ, "PYTHONPATH": str(root), "PYTHONDONTWRITEBYTECODE": "1"}
    result = subprocess.run(
        [sys.executable, "-c", script],
        cwd=tmp_path,
        env=env,
        capture_output=True,
        text=True,
        timeout=20,
        check=False,
    )
    assert result.returncode == 0, result.stderr
