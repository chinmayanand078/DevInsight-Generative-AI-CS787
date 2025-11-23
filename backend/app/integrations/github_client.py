from __future__ import annotations

import httpx
from pydantic import BaseModel


class GitHubConfig(BaseModel):
    api_base: str = "https://api.github.com"
    token: str
    repo: str  # format: owner/repo


class GitHubClient:
    """Minimal GitHub REST helper for posting PR and issue comments."""

    def __init__(self, config: GitHubConfig):
        self.config = config
        self._headers = {
            "Authorization": f"Bearer {self.config.token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        }

    async def post_pr_comment(self, pr_number: int, body: str) -> dict:
        url = f"{self.config.api_base}/repos/{self.config.repo}/issues/{pr_number}/comments"
        async with httpx.AsyncClient() as client:
            resp = await client.post(url, headers=self._headers, json={"body": body})
            resp.raise_for_status()
            return resp.json()

    async def post_commit_comment(self, sha: str, body: str, path: str | None = None, position: int | None = None) -> dict:
        url = f"{self.config.api_base}/repos/{self.config.repo}/commits/{sha}/comments"
        payload: dict = {"body": body}
        if path and position is not None:
            payload.update({"path": path, "position": position})

        async with httpx.AsyncClient() as client:
            resp = await client.post(url, headers=self._headers, json=payload)
            resp.raise_for_status()
            return resp.json()

