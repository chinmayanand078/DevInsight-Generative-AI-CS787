from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """
    Global configuration for DevInsight AI backend.
    Values are loaded from environment variables or a .env file.
    """

    # LLM / model configuration
    LLM_API_KEY: str | None = None
    MODEL_NAME: str = "llama-3-8b"

    # RAG / vector index paths
    FAISS_INDEX_PATH: str = "data/faiss_index"

    class Config:
        env_file = ".env"  # load variables from .env at project root, if present


# Single global settings instance
settings = Settings()
