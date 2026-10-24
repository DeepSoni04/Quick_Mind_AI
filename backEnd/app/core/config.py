import os
from typing import List, Optional, Union
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    APP_NAME: str = "QueryMind AI"
    ENVIRONMENT: str = "development"
    
    # MongoDB Application Database
    MONGODB_URI: str = "mongodb://localhost:27017"
    MONGODB_DATABASE: str = "querymind"
    
    # Security & Auth
    JWT_SECRET_KEY: str = "dev_jwt_secret_key_change_in_production_1234567890"
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440
    
    ADMIN_EMAIL: str = "admin@querymind.ai"
    ADMIN_PASSWORD: str = "admin123"
    
    # Symmetric credential encryption key (Fernet URL-safe base64 string)
    ENCRYPTION_KEY: str = "v8F5N9zT0yJ_3W2_3Z9a8K0L1M2N3O4P5Q6R7S8T9U0="
    
    # LLM Provider Configuration
    LLM_PROVIDER: str = "gemini"
    LLM_API_KEY: str = ""
    # Optional fallback LLM providers (leave blank if not available)
    OPENAI_API_KEY: Optional[str] = None
    ANTHROPIC_API_KEY: Optional[str] = None
    # OpenRouter — OpenAI-compatible gateway supporting many models
    OPENROUTER_API_KEY: Optional[str] = None
    OPENROUTER_MODEL: str = "mistralai/mistral-7b-instruct"
    # Comma-separated provider priority order for automatic fallback
    LLM_FALLBACK_ORDER: str = "gemini,openrouter,openai,anthropic,mock"
    
    # CORS
    CORS_ORIGINS: Union[str, List[str]] = "http://localhost:5173,http://127.0.0.1:5173"
    
    # Execution safety limits
    MIN_QUERY_ROWS: int = 1
    MAX_QUERY_ROWS: int = 1000
    MAX_ALLOWED_QUERY_ROWS: int = 5000
    MIN_QUERY_TIMEOUT_SECONDS: int = 1
    QUERY_TIMEOUT_SECONDS: int = 20
    MAX_QUERY_TIMEOUT_SECONDS: int = 120
    
    # URLs
    BACKEND_URL: str = "http://localhost:8000"
    FRONTEND_URL: str = "http://localhost:5173"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> List[str]:
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",") if i.strip()]
        elif isinstance(v, list):
            return v
        return ["http://localhost:5173", "http://127.0.0.1:5173"]

    def validate_production_secrets(self):
        """Ensure default development secrets are never used in production."""
        if self.ENVIRONMENT.lower() == "production":
            if self.JWT_SECRET_KEY == "dev_jwt_secret_key_change_in_production_1234567890" or len(self.JWT_SECRET_KEY) < 32:
                raise ValueError("Insecure JWT_SECRET_KEY detected for production environment.")
            if self.ENCRYPTION_KEY == "v8F5N9zT0yJ_3W2_3Z9a8K0L1M2N3O4P5Q6R7S8T9U0=":
                raise ValueError("Insecure ENCRYPTION_KEY detected for production environment.")
            if self.ADMIN_PASSWORD == "admin123":
                raise ValueError("Insecure ADMIN_PASSWORD detected for production environment.")


settings = Settings()
settings.validate_production_secrets()
