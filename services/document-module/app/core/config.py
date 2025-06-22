from pydantic import BaseSettings, Field
from typing import List

class Settings(BaseSettings):
    """Configuration for the Document Module service."""

    ALLOWED_ORIGINS: List[str] = Field(
        default=["http://localhost:3000", "http://localhost:8080"],
        env="ALLOWED_ORIGINS"
    )

    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()
