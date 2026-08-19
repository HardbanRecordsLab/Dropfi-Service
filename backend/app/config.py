from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    APP_NAME: str = "DROPIFY API"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True

    DATABASE_URL: str = "postgresql://dropify:dropify_pass@localhost:5432/dropify"
    REDIS_URL: str = "redis://localhost:6379/0"

    SECRET_KEY: str = "change-me-in-production-please-32-chars-min"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_DAYS: int = 7

    ANTHROPIC_API_KEY: str | None = None
    OPENAI_API_KEY: str | None = None

    STRIPE_SECRET_KEY: str | None = None
    STRIPE_WEBHOOK_SECRET: str | None = None
    STRIPE_PUBLISHABLE_KEY: str | None = None
    FRONTEND_URL: str = "http://localhost:3000"

    SMTP_HOST: str | None = None
    SMTP_PORT: int = 587
    SMTP_USER: str | None = None
    SMTP_PASSWORD: str | None = None
    SENDER_EMAIL: str = "noreply@dropify.app"

    # n8n automation (self-hosted workflow engine)
    N8N_WEBHOOK_URL: str = ""      # e.g. http://n8n:5678/webhook
    N8N_WEBHOOK_SECRET: str = ""   # HMAC secret shared with n8n workflows
    N8N_INBOUND_KEY: str = ""      # API key for n8n → DROPIFY /api/n8n/trigger

    CORS_ORIGINS: list[str] = [
        "http://localhost:3000",
        "http://localhost:8080",
    ]

    PLATFORM_FEE_RATE: float = 0.08
    FEE_RATE_TOP: float = 0.05
    FEE_RATE_NEW: float = 0.12
    TOP_RATING_MIN: float = 4.8
    TOP_RATING_COUNT_MIN: int = 20
    NEW_RATING_COUNT_MAX: int = 3
    REFERRAL_RATE_L1: float = 0.02
    REFERRAL_RATE_L2: float = 0.01
    REFERRAL_MONTHS: int = 12
    EMBEDDING_DIM: int = 1536

    ADMIN_EMAIL: str = "admin@dropify.app"
    ADMIN_PASSWORD: str = "admin123"

    SEED_DEMO_DATA: bool = False
    DAILY_SUMMARY_ENABLED: bool = True

    @property
    def cors_origins(self) -> list[str]:
        extra = getattr(self, "CORS_ORIGINS_EXTRA", "")
        origins = list(self.CORS_ORIGINS)
        if extra:
            origins += [o.strip() for o in extra.split(",") if o.strip()]
        return origins


settings = Settings()
