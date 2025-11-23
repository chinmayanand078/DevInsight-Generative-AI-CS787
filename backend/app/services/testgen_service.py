import json
from pathlib import Path
from textwrap import dedent, indent

from backend.app.config import settings
from backend.app.llm.client import LLMClient
from backend.app.schemas import (
    GeneratedTest,
    TestGenRequest,
    TestGenResponse,
)
from backend.app.static_analysis.analyzer import (
    detect_edge_cases,
    estimate_complexity,
    extract_function_signatures,
)
from backend.app.testing.coverage_runner import (
    build_coverage_report,
    run_pytest_with_coverage,
    summarize_coverage,
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


async def _llm_test_suggestions(code: str, analysis: dict) -> list[dict]:
    if settings.LLM_PROVIDER == "mock" or not settings.LLM_API_KEY:
        return []

    prompt = dedent(
        f"""
        You are an expert Python test author. Given the module code and the static analysis
        summary, propose targeted pytest test cases. Respond strictly as JSON with the
        schema: {{"tests": [{{"name": "test_name", "code": "def test...", "description": "why this test"}}]}}.

        Module code:\n{code}

        Static analysis:
        {json.dumps(analysis, indent=2)}
        """
    ).strip()

    try:
        client = LLMClient()
        raw = await client.generate_tests(prompt)
        parsed = json.loads(raw)
        return parsed.get("tests", [])
    except Exception:
        return []


def _append_llm_tests(base_code: str, llm_tests: list[dict]) -> str:
    if not llm_tests:
        return base_code

    rendered: list[str] = [base_code.rstrip(), "", "# --- Model-suggested tests ---"]
    for idx, test in enumerate(llm_tests, start=1):
        description = test.get("description")
        name = test.get("name") or f"model_suggested_test_{idx}"
        code = test.get("code") or ""

        if description:
            rendered.append(f"# {description}")
        if code.strip():
            rendered.append(code.strip())
        else:
            rendered.append(f"def {name}():\n    assert True  # placeholder from model")
        rendered.append("")

    return "\n".join(rendered).rstrip() + "\n"


async def generate_tests(request: TestGenRequest) -> TestGenResponse:
    """
    Generate pytest files using static analysis with optional LLM enrichment and coverage runs.
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

    sources = ["static-analysis"]

    llm_tests = await _llm_test_suggestions(code, analysis)
    if llm_tests:
        test_code = _append_llm_tests(test_code, llm_tests)
        sources.append("llm")

    coverage_summary = None
    coverage_report = None
    if request.coverage_goal:
        result = run_pytest_with_coverage(request.file_path, code, test_code)
        coverage_report = build_coverage_report(result, goal=request.coverage_goal)
        coverage_summary = summarize_coverage(result, report=coverage_report)

    test_obj = GeneratedTest(
        file_path=test_file,
        test_code=test_code,
        coverage_summary=coverage_summary,
        coverage_report=coverage_report,
        sources=sources,
        model_used=settings.MODEL_NAME if "llm" in sources else None,
    )

    return TestGenResponse(tests=[test_obj])

