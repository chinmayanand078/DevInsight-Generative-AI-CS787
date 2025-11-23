from __future__ import annotations

import os
import subprocess
import sys
import tempfile
from pathlib import Path
from textwrap import dedent


class CoverageResult(dict):
    """Simple mapping wrapper to hold coverage outputs."""


def run_pytest_with_coverage(module_path: str, code: str, test_code: str) -> CoverageResult:
    """
    Write the target code + generated tests to a temp workspace and run pytest with
    coverage enabled. Returns stderr/stdout and the exit code for transparency.
    """

    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_base = Path(tmpdir)
        target_file = tmp_base / module_path
        target_file.parent.mkdir(parents=True, exist_ok=True)
        target_file.write_text(code, encoding="utf-8")

        tests_dir = tmp_base / "tests"
        tests_dir.mkdir(parents=True, exist_ok=True)
        test_file = tests_dir / f"test_{Path(module_path).stem}.py"
        test_file.write_text(test_code, encoding="utf-8")

        env = os.environ.copy()
        env["PYTHONPATH"] = f"{tmp_base}:{env.get('PYTHONPATH','')}"

        cmd = [
            sys.executable,
            "-m",
            "pytest",
            "-q",
            "--disable-warnings",
            "--maxfail=1",
            "--cov",
            Path(module_path).with_suffix("").as_posix().replace("/", "."),
            "--cov-report",
            "term-missing",
            str(test_file),
        ]

        proc = subprocess.run(cmd, cwd=tmp_base, capture_output=True, text=True, env=env)
        return CoverageResult(
            stdout=proc.stdout,
            stderr=proc.stderr,
            returncode=proc.returncode,
        )


def summarize_coverage(result: CoverageResult) -> str:
    header = "Pytest/coverage execution"
    body = dedent(
        f"""
        exit code: {result.get('returncode')}
        --- stdout ---
        {result.get('stdout','').strip()}
        --- stderr ---
        {result.get('stderr','').strip()}
        """
    ).strip()
    return f"{header}\n{body}\n"

