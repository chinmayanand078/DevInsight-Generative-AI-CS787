import subprocess
from pathlib import Path
from typing import List, Tuple


ALLOWED_EXTENSIONS = {".md", ".py", ".txt"}
EXCLUDE_DIRS = {".git", "__pycache__", "node_modules", "backend/app/rag/index"}


def load_repo_text(base_path: str = ".") -> list[tuple[str, dict]]:
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


def load_git_history(base_path: str = ".", max_commits: int = 25) -> List[Tuple[str, dict]]:
    """
    Read recent Git history (subject + body + patch) to enrich RAG context with
    change intent. Falls back gracefully if Git is unavailable.
    """

    repo_path = Path(base_path)
    if not (repo_path / ".git").exists():
        return []

    cmd = [
        "git",
        "-C",
        str(repo_path),
        "log",
        f"-{max_commits}",
        "--stat",
        "--patch",
    ]

    try:
        result = subprocess.run(
            cmd,
            check=True,
            text=True,
            capture_output=True,
            encoding="utf-8",
            errors="ignore",
        )
    except (OSError, subprocess.CalledProcessError):
        return []

    log_text = result.stdout.strip()
    if not log_text:
        return []

    return [
        (
            log_text,
            {
                "source": "git_history",
                "description": f"Last {max_commits} commits (subject, body, patch)",
            },
        )
    ]

