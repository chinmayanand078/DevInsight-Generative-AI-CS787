from __future__ import annotations

import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path
from textwrap import dedent


class CoverageResult(dict):
    """Simple mapping wrapper to hold coverage outputs."""


def _coverage_threshold(goal: str | None) -> float | None:
    if goal is None:
        return None

    normalized = goal.lower()
    mapping = {
        "smoke": 25.0,
        "basic": 50.0,
        "strong": 80.0,
        "max": 95.0,
    }
    return mapping.get(normalized)


def parse_coverage(stdout: str):
    """Extract overall percent and missing-line hints from pytest --cov output."""

    percent = None
    missing: list[str] = []

    total_match = re.search(r"TOTAL\s+\d+\s+\d+\s+(\d+)%", stdout)
    if total_match:
        percent = float(total_match.group(1))

    missing_pattern = re.compile(r"^(?P<name>\S+)\s+\d+\s+\d+\s+\d+%\s+(?P<missing>.+)$")
    for line in stdout.splitlines():
        match = missing_pattern.match(line.strip())
        if match and "TOTAL" not in match.group("name"):
            missing.append(f"{match.group('name')}: {match.group('missing')}")

    return percent, missing


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


def build_coverage_report(result: CoverageResult, goal: str | None = None):
    percent, missing = parse_coverage(result.get("stdout", ""))
    threshold = _coverage_threshold(goal)

    goal_met: bool | None
    if percent is not None and threshold is not None:
        goal_met = percent >= threshold
    else:
        goal_met = None

    summary_lines = ["Pytest/coverage execution"]
    summary_lines.append(f"exit code: {result.get('returncode')}")
    if percent is not None:
        summary_lines.append(f"coverage: {percent:.1f}%")
    if threshold is not None:
        summary_lines.append(f"goal '{goal}' (>= {threshold}%) => {'met' if goal_met else 'not met'}")
    if missing:
        summary_lines.append("missing lines: " + "; ".join(missing))

    summary_lines.append("--- stdout ---")
    summary_lines.append(result.get("stdout", "").strip())
    summary_lines.append("--- stderr ---")
    summary_lines.append(result.get("stderr", "").strip())

    return {
        "percent": percent,
        "missing": missing or None,
        "goal": goal,
        "goal_met": goal_met,
        "stdout": result.get("stdout"),
        "stderr": result.get("stderr"),
        "returncode": result.get("returncode"),
        "summary": "\n".join(summary_lines).strip() + "\n",
    }


def summarize_coverage(result: CoverageResult, report: dict | None = None) -> str:
    if report and report.get("summary"):
        return report["summary"]

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

