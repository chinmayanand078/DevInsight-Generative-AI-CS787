"""End-to-end GitHub Action helper.

This script is meant to be executed inside a GitHub Actions runner after the
repository has been checked out. It will:

1. Parse the event payload to identify the PR number and title.
2. Collect changed files in the workspace (using the base ref if available).
3. Run the in-repo review pipeline to generate comments.
4. Post a summary comment back to the PR.

Usage (inside an Action step):

```bash
python -m backend.app.integrations.github_workflow \
  --repo "$GITHUB_REPOSITORY" \
  --token "$GITHUB_TOKEN" \
  --event-path "$GITHUB_EVENT_PATH" \
  --api-base "https://api.github.com"
```
"""

from __future__ import annotations

import argparse
import asyncio
import json
import logging
import subprocess
from pathlib import Path
from typing import List

from backend.app.integrations.github_client import GitHubClient, GitHubConfig
from backend.app.schemas import FileDiff, ReviewRequest
from backend.app.services.review_service import run_review

logger = logging.getLogger(__name__)


def _read_event(path: Path) -> dict:
    """Read and parse the GitHub event payload JSON if present."""
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}


def _has_ref(ref: str) -> bool:
    """Return True if the given git ref exists locally."""
    try:
        subprocess.run(
            ["git", "rev-parse", "--verify", ref],
            check=True,
            capture_output=True,
            text=True,
        )
        return True
    except subprocess.CalledProcessError:
        return False


def _ensure_ref_available(ref: str) -> None:
    """Fetch the requested ref, tolerating failures for forked PRs."""
    try:
        subprocess.run(
            ["git", "fetch", "--no-tags", "--depth", "200", "origin", ref],
            check=True,
            capture_output=True,
            text=True,
        )
    except subprocess.CalledProcessError:
        # Best-effort: continue even if fetch fails (e.g., forked PRs without access)
        logger.warning("Unable to fetch %s; continuing with local history", ref)


def _resolve_base_ref(base_ref: str | None, base_sha: str | None) -> str:
    """Select the best available base ref/sha to diff against."""
    candidates: List[str] = []
    if base_sha:
        candidates.append(base_sha)
    if base_ref:
        candidates.extend([base_ref, f"origin/{base_ref}"])
    candidates.append("origin/master")

    for candidate in candidates:
        if not _has_ref(candidate):
            # Attempt to fetch the branch/sha before retrying
            ref_to_fetch = candidate.removeprefix("origin/")
            _ensure_ref_available(ref_to_fetch)
        if _has_ref(candidate):
            return candidate

    # Fallback: diff against previous commit if nothing else is available
    return "HEAD^"


def _changed_files(base_ref: str | None, base_sha: str | None) -> List[str]:
    """Return the list of files changed between the base ref and HEAD."""
    base = _resolve_base_ref(base_ref, base_sha)
    cmd = ["git", "diff", "--name-only", f"{base}...HEAD"]
    try:
        result = subprocess.run(cmd, check=True, text=True, capture_output=True)
    except subprocess.CalledProcessError:
        return []

    return [line.strip() for line in result.stdout.splitlines() if line.strip()]


def _read_file(path: Path) -> str:
    """Safely read a text file, returning an empty string on failure."""
    try:
        return path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return ""


async def main(args: argparse.Namespace) -> None:
    event = _read_event(Path(args.event_path))
    pr = event.get("pull_request", {})

    pr_number = pr.get("number") or pr.get("id") or 0
    pr_title = pr.get("title") or "Auto DevInsight review"

    base_info = pr.get("base", {})
    base_ref = base_info.get("ref") or args.base_ref
    base_sha = base_info.get("sha")

    files = _changed_files(base_ref, base_sha)
    diffs: List[FileDiff] = []

    for filename in files:
        file_path = Path(filename)
        new_code = _read_file(file_path)
        if not new_code:
            continue
        diffs.append(FileDiff(filename=filename, new_code=new_code, old_code=None))

    if not diffs:
        logger.info("No changes detected; skipping comment")
        return

    request = ReviewRequest(
        pr_title=pr_title,
        pr_number=int(pr_number),
        repo_name=args.repo,
        diffs=diffs,
    )

    response = await run_review(request)

    summary_lines = ["## DevInsight automated review", ""]
    if response.comments:
        for c in response.comments:
            summary_lines.append(
                f"- `{c.severity}` {c.filename}:{c.line} — {c.message}"
            )
    else:
        summary_lines.append("No findings detected.")

    client = GitHubClient(
        GitHubConfig(api_base=args.api_base, token=args.token, repo=args.repo)
    )
    await client.post_pr_comment(pr_number=int(pr_number), body="\n".join(summary_lines))


def parse_args() -> argparse.Namespace:
    """Parse CLI arguments for running the workflow inside Actions."""
    parser = argparse.ArgumentParser(description="Run DevInsight review inside Actions")
    parser.add_argument("--repo", required=True, help="owner/repo")
    parser.add_argument("--token", required=True, help="GitHub token")
    parser.add_argument("--event-path", required=True, help="Path to GITHUB_EVENT_PATH")
    parser.add_argument("--api-base", default="https://api.github.com")
    parser.add_argument(
        "--base-ref",
        default=None,
        help="Base ref for git diff (defaults to PR base or origin/master)",
    )
    return parser.parse_args()


if __name__ == "__main__":
    asyncio.run(main(parse_args()))
