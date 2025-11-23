from pathlib import Path


ALLOWED_EXTENSIONS = {".md", ".py", ".txt"}
EXCLUDE_DIRS = {".git", "__pycache__", "node_modules", "backend/app/rag/index"}


def load_repo_text(base_path: str = "."):
    """
    Read repository text content (Markdown + Python + text) into a list of
    (content, metadata) tuples. Traversal is bounded to small text files to avoid
    accidentally slurping binaries or huge artifacts.
    """

    base = Path(base_path)
    targets = []

    for path in base.rglob("*"):
        if path.is_dir():
            if any(part in EXCLUDE_DIRS for part in path.parts):
                continue
            continue

        if path.suffix.lower() not in ALLOWED_EXTENSIONS:
            continue

        if any(part in EXCLUDE_DIRS for part in path.parts):
            continue

        try:
            text = path.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue

        # Skip extremely small or large files that add little search value
        if len(text) < 20 or len(text) > 200_000:
            continue

        rel_path = str(path.relative_to(base))
        targets.append((text, {"source": rel_path}))

    return targets

