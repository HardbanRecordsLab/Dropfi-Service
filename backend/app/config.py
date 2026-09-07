from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    APP_NAME: str = "DROPIFY API"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False

    DATABASE_URL: str = "postgresql://dropify:dropify_pass@localhost:5432/dropify"
    REDIS_URL: str = "redis://localhost:6379/0"

    SECRET_KEY: str = "change-me-in-production-please-32-chars-min"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_DAYS: int = 7

    ANTHROPIC_API_KEY: str | None = None
    OPENAI_API_KEY: str | None = None

    # LLM via OpenRouter (OpenAI-compatible). Free models by default; swap to a
    # cheap paid model in .env once volume justifies it. Embeddings stay on the
    # local zero-cost fallback unless OPENAI_API_KEY is also set.
    OPENROUTER_API_KEY: str = ""
    LLM_BASE_URL: str = "https://openrouter.ai/api/v1"
    LLM_MODEL: str = "deepseek/deepseek-chat-v3-0324:free"
    LLM_MODEL_FALLBACK: str = "meta-llama/llama-3.3-70b-instruct:free"
    LLM_MAX_TOKENS: int = 1200
    LLM_TIMEOUT: int = 40
    LLM_APP_URL: str = "https://dropify.hardbanrecordslab.online"
    LLM_APP_NAME: str = "DROPIFY"

    STRIPE_SECRET_KEY: str | None = None
    STRIPE_WEBHOOK_SECRET: str | None = None
    STRIPE_PUBLISHABLE_KEY: str | None = None
    FRONTEND_URL: str = "http://localhost:3000"

    SMTP_HOST: str | None = None
    SMTP_PORT: int = 587
    SMTP_USER: str | None = None
    SMTP_PASSWORD: str | None = None
    SENDER_EMAIL: str = "dropify@hardbanrecordslab.online"

    # Legal / Ownership
    PLATFORM_OWNER: str = "HardbanRecords Lab"
    PLATFORM_OWNER_LOCATION: str = "Wiercień, Poland"
    SUPPORT_EMAIL: str = "dropify@hardbanrecordslab.online"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        import warnings
        defaults = []
        if self.SECRET_KEY == "change-me-in-production-please-32-chars-min":
            defaults.append("SECRET_KEY")
        if self.ADMIN_PASSWORD == "admin123":
            defaults.append("ADMIN_PASSWORD")

        if defaults and not self.DEBUG:
            raise ValueError(
                f"Cannot start with default values in production mode. "
                f"Set real values in .env for: {', '.join(defaults)}"
            )
        elif defaults:
            warnings.warn(
                f"Using default values ({', '.join(defaults)}) — set real values in .env for production!",
                stacklevel=2,
            )

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
    CELERY_TASK_ALWAYS_EAGER: bool = False   # tests set this True (run tasks in-process)

    # Invoicing / VAT
    PLATFORM_NIP: str = ""              # Polish tax ID (NIP) — required for real invoices
    PLATFORM_VAT_EU: str = ""           # VAT-UE number for cross-border EU invoices
    PLATFORM_REGISTRATION: str = ""     # CEIDG/KRS registration number
    PLATFORM_ADDRESS: str = "Wiercień, Poland"
    PLATFORM_NAME: str = "HardbanRecords Lab"
    INVOICE_PREFIX: str = "DROPIFY"
    INVOICE_VAT_RATE: float = 0.23      # 23% VAT for PL domestic
    INVOICE_CURRENCY: str = "PLN"
    INVOICE_PAYMENT_DAYS: int = 14

    # Portal Radar — global scan of external job portals (official APIs / RSS only)
    RADAR_ENABLED: bool = True
    RADAR_BOT_EMAIL: str = "radar@dropify.app"   # owns jobs imported from external leads
    RADAR_SCAN_INTERVAL_HOURS: int = 6
    RADAR_MAX_PER_SOURCE: int = 50
    RADAR_HTTP_TIMEOUT: int = 15
    # Connectors parked until their public endpoint is re-verified (comma-separated slugs)
    RADAR_DISABLED_SOURCES: str = "useme,justjoinit"
    ADZUNA_APP_ID: str = ""              # optional — enables the Adzuna connector
    ADZUNA_APP_KEY: str = ""
    USAJOBS_API_KEY: str = ""            # optional — enables the USAJOBS connector
    USAJOBS_EMAIL: str = ""
    GITHUB_TOKEN: str = ""               # optional — raises GitHub talent-search rate limit

    @property
    def cors_origins(self) -> list[str]:
        extra = getattr(self, "CORS_ORIGINS_EXTRA", "")
        origins = list(self.CORS_ORIGINS)
        if extra:
            origins += [o.strip() for o in extra.split(",") if o.strip()]
        return origins


settings = Settings()
