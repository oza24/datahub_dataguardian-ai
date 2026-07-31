"""
Central configuration. All tunables (thresholds, model names, URLs) live here
so no agent or service hardcodes an environment-specific value.
"""
import os
from dotenv import load_dotenv

load_dotenv()


class Settings:
    # LLM
    GEMINI_API_KEY: str | None = os.getenv("GEMINI_API_KEY")
    GEMINI_CHAT_MODEL: str = os.getenv("GEMINI_CHAT_MODEL", "gemini-2.0-flash")
    GEMINI_EMBEDDING_MODEL: str = os.getenv("GEMINI_EMBEDDING_MODEL", "gemini-embedding-001")

    # DataHub GMS
    DATAHUB_GMS_URL: str = os.getenv("DATAHUB_GMS_URL", "http://localhost:8080")
    DATAHUB_GMS_TOKEN: str | None = os.getenv("DATAHUB_GMS_TOKEN")
    GRAPHQL_TIMEOUT_SECONDS: int = int(os.getenv("GRAPHQL_TIMEOUT_SECONDS", "15"))

    # Semantic matching confidence thresholds (0-1). Below threshold => ask, never guess.
    TABLE_MATCH_CONFIDENCE_THRESHOLD: float = float(os.getenv("TABLE_MATCH_CONFIDENCE_THRESHOLD", "0.68"))
    FIELD_MATCH_CONFIDENCE_THRESHOLD: float = float(os.getenv("FIELD_MATCH_CONFIDENCE_THRESHOLD", "0.72"))
    INTENT_CONFIDENCE_THRESHOLD: float = float(os.getenv("INTENT_CONFIDENCE_THRESHOLD", "0.55"))

    # Self-healing mutation retries
    MAX_MUTATION_RETRIES: int = int(os.getenv("MAX_MUTATION_RETRIES", "2"))

    # Search
    DATASET_SEARCH_CANDIDATE_LIMIT: int = int(os.getenv("DATASET_SEARCH_CANDIDATE_LIMIT", "10"))


settings = Settings()
