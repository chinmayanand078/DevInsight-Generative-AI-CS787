import re
from backend.app.schemas import TestGenRequest, TestGenResponse, GeneratedTest
from backend.app.static_analysis.analyzer import (
    extract_function_signatures,
    detect_edge_cases,
    estimate_complexity,
)
from backend.app.llm.prompts import build_testgen_prompt


async def generate_tests(request: TestGenRequest) -> TestGenResponse:
    """
    Generate unit tests using LLM + static analysis hints.
    (Mock LLM output for now — will integrate real model later.)
    """

    code = request.code

    # 1) Static Analysis
    analysis = {
        "signatures": extract_function_signatures(code),
        "edge_cases": detect_edge_cases(code),
        "complexity": estimate_complexity(code),
    }

    # 2) Build prompt (not used yet but ready for real LLM)
    prompt = build_testgen_prompt(code, analysis)

    # TEMP mock LLM output so system works end-to-end
    llm_output = """TEST_FILE:
tests/test_generated.py
TEST_CODE:
import pytest

def test_add():
    assert add(2, 3) == 5
"""

    # 3) Parse LLM output
    match = re.search(
        r"TEST_FILE:\s*(.*?)\s*TEST_CODE:\s*(.*)",
        llm_output,
        flags=re.DOTALL,
    )

    if not match:
        return TestGenResponse(tests=[])

    file_path = match.group(1).strip()
    test_code = match.group(2).strip()

    test_obj = GeneratedTest(
        file_path=file_path,
        test_code=test_code,
    )

    return TestGenResponse(tests=[test_obj])

