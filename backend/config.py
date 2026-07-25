import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    PROJECT_NAME: str = "Zepto Reviews AI"
    API_V1_STR: str = "/api/v1"
    ZEPTO_PACKAGE_NAME: str = "com.zepto.customer"
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./zepto_reviews.db")
    PLAYSTORE_DEFAULT_COUNT: int = 50
    PII_REDACTION_MASK: str = "[REDACTED_PII]"

    # Google AI Studio Gemini API Rate Limits & Model Configuration
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    GEMINI_MODEL_NAME: str = "gemini-flash-latest"   # Active Google AI Studio model
    GOOGLE_AI_STUDIO_RPM_LIMIT: int = 60            # 60 Requests Per Minute
    GOOGLE_AI_STUDIO_TPM_LIMIT: int = 100000        # 100K Input Tokens Per Minute
    LLM_BATCH_SIZE: int = 10                        # 10 Reviews per LLM batch request
    LLM_REQUEST_DELAY_SECONDS: float = 1.0          # 1 second delay between batch calls

    class Config:
        case_sensitive = True

settings = Settings()
