from pathlib import Path
from textwrap import indent

from backend.app.schemas import TestGenRequest, TestGenResponse, GeneratedTest
from backend.app.static_analysis.analyzer import (
    extract_function_signatures,
    detect_edge_cases,
    estimate_complexity,
)


def _guess_value(arg_name: str) -> str:
    lowered = arg_name.lower()
    if "path" in lowered:
        return "\"/tmp/example\""
    if any(token in lowered for token in ["count", "size", "idx", "index", "num"]):
        return "1"
    if any(token in lowered for token in ["flag", "is_", "has_", "enabled"]):
        return "True"
    if any(token in lowered for token in ["list", "items", "values"]):
        return "[]"
    if any(token in lowered for token in ["dict", "mapping", "config"]):
        return "{}"
    return "\"sample\""


def _build_test_body(func_name: str, args: list[str], edge_cases: list[str]) -> str:
    setup_lines = [f"{arg}_value = {_guess_value(arg)}" for arg in args]
    if args:
        arg_list = ", ".join([f"{a}_value" for a in args])
        call_line = f"result = module.{func_name}({arg_list})"
    else:
        call_line = f"result = module.{func_name}()"

    assertions = ["assert result is not None"]
    if edge_cases:
        assertions.append("# Edge cases noted: " + ", ".join(edge_cases))

    body_lines = setup_lines + [call_line] + assertions
    return "\n".join(body_lines)


def _build_test_file(module_path: str, signatures: list[dict], edge_cases: list[str]) -> str:
    lines = [
        "import importlib",
        "import pytest",
        f"module = importlib.import_module('{module_path}')",
        "",
    ]

    for sig in signatures:
        func_name = sig.get("name", "target")
        args = sig.get("args", [])
        test_name = f"test_{func_name}_returns_value"
        body = _build_test_body(func_name, args, edge_cases)
        lines.append(f"def {test_name}():")
        lines.append(indent(body, "    "))
        lines.append("")

    if not signatures:
        lines.append("def test_placeholder():")
        lines.append("    pytest.skip('No callable functions detected; add tests manually.')")

    return "\n".join(lines).rstrip() + "\n"


async def generate_tests(request: TestGenRequest) -> TestGenResponse:
    """
    Generate deterministic pytest files using static analysis (no external LLM).
    """

    code = request.code

    analysis = {
        "signatures": extract_function_signatures(code),
        "edge_cases": detect_edge_cases(code),
        "complexity": estimate_complexity(code),
    }

    module_path = Path(request.file_path).with_suffix("").as_posix().replace("/", ".")
    test_file = f"tests/test_{Path(request.file_path).stem}.py"
    test_code = _build_test_file(module_path, analysis["signatures"], analysis["edge_cases"])

    test_obj = GeneratedTest(
        file_path=test_file,
        test_code=test_code,
    )

    return TestGenResponse(tests=[test_obj])

