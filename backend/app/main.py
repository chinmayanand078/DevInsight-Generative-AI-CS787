from fastapi import FastAPI

from .schemas import (
    HealthResponse,
    ReviewRequest,
    ReviewResponse,
    TestGenRequest,
    TestGenResponse
)
from .services.review_service import run_review
from .services.testgen_service import generate_tests   # ⬅️ THIS WAS MISSING

app = FastAPI(
    title="DevInsight AI Backend",
    version="0.2.0",
    description="Context-aware code review & knowledge assistant backend.",
)


@app.get("/health", response_model=HealthResponse)
def health_check() -> HealthResponse:
    """Simple health check endpoint."""
    return HealthResponse(status="ok")


@app.post("/review", response_model=ReviewResponse)
async def review_endpoint(request: ReviewRequest):
    """
    Accepts PR details + diffs and returns review comments.
    """
    response = await run_review(request)
    return response


@app.post("/generate-tests", response_model=TestGenResponse)
async def generate_tests_endpoint(request: TestGenRequest):
    """
    Generates unit tests for the submitted code snippet.
    """
    return await generate_tests(request)


