import ast


def extract_function_signatures(code: str):
    """
    Returns a list of functions with names and args.
    """
    signatures = []
    try:
        tree = ast.parse(code)
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                arg_names = [a.arg for a in node.args.args]
                signatures.append({"name": node.name, "args": arg_names})
    except SyntaxError:
        pass

    return signatures


def detect_edge_cases(code: str):
    """
    Naive heuristic: detect conditions and branch points.
    """
    edge_cases = []
    keywords = ["if ", "try:", "except", "raise", "return None", "len(", "== 0", "< 0", "> 0"]
    for k in keywords:
        if k in code:
            edge_cases.append(k.strip())
    return edge_cases


def estimate_complexity(code: str):
    """
    Rough cyclomatic complexity = count of branching nodes.
    """
    try:
        tree = ast.parse(code)
        return sum(isinstance(node, (ast.If, ast.For, ast.While, ast.Try)) for node in ast.walk(tree))
    except SyntaxError:
        return 1

