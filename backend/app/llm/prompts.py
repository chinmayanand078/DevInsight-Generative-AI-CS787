from textwrap import dedent
from backend.app.schemas import ReviewRequest


def build_review_prompt(request: ReviewRequest, rag_context: list[dict]) -> str:
    """
    Builds an LLM prompt using PR metadata, file diffs, and RAG context.
    """

    # Build a context string from FAISS search
    context_str = ""
    if rag_context:
        context_str += "Relevant repository context:\n"
        for item in rag_context:
            context_str += f"- From: {item.get('source', 'unknown')}\n"
        context_str += "\n"

    # Build diff summary
    diffs_str = ""
    for diff in request.diffs:
        diffs_str += f"FILE: {diff.filename}\n"
        diffs_str += f"NEW CODE:\n{diff.new_code}\n"
        diffs_str += "-" * 60 + "\n"

    prompt = f"""
    You are an expert senior software engineer doing a precise code review.
    Be strict, factual, and constructive.

    Pull Request Title: {request.pr_title}
    Repository: {request.repo_name}
    PR Number: {request.pr_number}

    {context_str}

    Code to review:
    {diffs_str}

    Task:
    1. Identify issues, code smells, anti-patterns, missing documentation, edge cases, and test gaps.
    2. For each finding, return:
       - filename
       - line number (best estimate if unknown)
       - severity (info | warning | critical)
       - message (concise fix recommendation)

    Respond in this format (no extra commentary):
    FINDINGS:
    - filename: <file> | line: <num> | severity: <severity> | message: <text>
    """

    return dedent(prompt).strip()

def build_testgen_prompt(code: str, analysis: dict) -> str:
    """
    Builds an LLM prompt for generating unit tests based on code + analysis hints.
    """

    sigs = analysis.get("signatures", [])
    edges = analysis.get("edge_cases", [])
    complexity = analysis.get("complexity", 1)

    sig_text = "\n".join([f"- {s['name']}({', '.join(s['args'])})" for s in sigs]) or "None"
    edge_text = "\n".join([f"- {e}" for e in edges]) or "None"

    prompt = f"""
    You are an expert Python engineer generating **unit tests** using pytest.

    Code under test:
    --------------
    {code}
    --------------

    Function signatures detected:
    {sig_text}

    Edge cases to consider:
    {edge_text}

    Estimated cyclomatic complexity: {complexity}

    Requirements:
    - Use pytest style (no unittest class)
    - Include boundary cases + error handling + branches
    - Avoid mocking unless necessary
    - Make tests deterministic
    - Use clear variable names
    - Do not add explanations, comments, or markdown

    Output format (strict):
    TEST_FILE:
    <file_name>
    TEST_CODE:
    <full test file content>
    """

    return prompt.strip()

