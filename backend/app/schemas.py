from pydantic import BaseModel
from typing import List, Optional


class FileDiff(BaseModel):
    filename: str
    old_code: Optional[str] = None
    new_code: Optional[str] = None


class ReviewRequest(BaseModel):
    pr_title: str
    pr_number: int
    repo_name: str
    diffs: List[FileDiff]


class ReviewComment(BaseModel):
    filename: str
    line: int
    message: str
    severity: str = "info"
    source_link: Optional[str] = None


class ReviewResponse(BaseModel):
    comments: List[ReviewComment]


class HealthResponse(BaseModel):
    status: str

class TestGenRequest(BaseModel):
    file_path: str
    code: str
    coverage_goal: Optional[str] = None


class GeneratedTest(BaseModel):
    file_path: str
    test_code: str
    coverage_summary: Optional[str] = None


class TestGenResponse(BaseModel):
    tests: List[GeneratedTest]

