import os
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # --- Database ---
    DATABASE_URL: str = "sqlite:///./local.db"

    # --- Object Storage (S3-compatible) ---
    S3_BUCKET: str = ""
    S3_ACCESS_KEY_ID: str = ""
    S3_SECRET_ACCESS_KEY: str = ""
    S3_REGION: str = "us-east-1"

    # --- Base URLs ---
    AFFIL_BASE_URL: str = "https://example.com"
    APP_BASE_URL: str = "http://localhost:5000"
    PUBLIC_BASE_URL: str = "http://localhost:5000"

    # --- JWT / Session ---
    JWT_SECRET: str = "your-secret-key-here"
    SESSION_SECRET: str = "your-session-secret-here"
    ADMIN_SECRET: str = "change_me_now"

    # --- SerpAPI ---
    SERPAPI_KEY: str = ""
    SERPAPI_HL: str = "fr"
    SERPAPI_GL: str = "FR"
    SERPAPI_CACHE_TTL: int = 3600
    SERPAPI_MAX_RESULTS: int = 10

    # --- Meta / Instagram Graph API ---
    META_APP_ID: str = ""
    META_APP_SECRET: str = ""
    META_VERIFY_TOKEN: str = "change_me"
    META_GRAPH_VERSION: str = "v21.0"
    META_SCOPES: str = (
        "pages_show_list,"
        "pages_read_engagement,"
        "instagram_basic,"
        "instagram_content_publish"
    )
    META_REDIRECT_URI: str = ""

    # --- AI Orchestrator / Autopilot ---
    FEATURE_AUTOPILOT: bool = False
    FEATURE_RISKBOT: bool = False
    FEATURE_SUPPORTBOT: bool = False

    AI_TICK_INTERVAL_MIN: int = 10
    AI_MAX_ACTIONS_PER_TICK: int = 5
    AI_CONFIDENCE_THRESHOLD: float = 0.55
    AI_DRY_RUN: bool = False
    AI_OBJECTIVE: str = "revenue_ctr_safe"
    AI_LOOKBACK_DAYS: int = 7
    AI_MIN_CTR: float = 0.008
    AI_MIN_QUALITY: float = 0.70
    AI_MAX_RISK: float = 0.20

    # --- Partner / Payouts ---
    PAYOUT_MIN_EUR: float = 10.0
    PAYOUT_RESERVE_PCT: float = 0.30
    PAYOUT_RELEASE_DAYS: int = 30
    PAYOUT_WEEKDAY: int = 1  # Lundi
    PAYOUT_APPROVAL_THRESHOLD_EUR: float = 200.0
    PAYOUT_METHODS: str = "paypal,bank"

    # --- Offers / Revshare ---
    DEFAULT_EPC_EUR: float = 0.25
    OFFER_MODE: str = "cpc_dynamic"
    CPC_DEFAULT_EUR: float = 0.10
    CPC_MIN_EUR: float = 0.06
    CPC_MAX_EUR: float = 0.12
    CPC_SAFETY_MARGIN_EUR: float = 0.05
    REVSHARE_BASE_PCT: float = 0.40

    # --- Affiliate ---
    AFF_DEFAULT_CURRENCY: str = "EUR"
    AFF_ACCEPT_PENDING: bool = True
    AFF_MAX_AGE_DAYS: int = 45
    AFF_SUBID_FORMAT: str = "pid:aid:clk"
    AFF_ALLOWLIST_IPS: str = ""

    # --- Risk Management ---
    RISK_VELOCITY_MAX_CLICKS_10M: int = 40
    RISK_HOLD_DAYS: int = 30

    # --- Ticket System ---
    TICKET_AUTO_CLOSE_DAYS: int = 5

    # --- Brevo / Email ---
    BREVO_API_KEY: str = ""
    EMAIL_FROM: str = "noreply@contentflow.app"
    EMAIL_FROM_NAME: str = "ContentFlow"

    # --- Supadata ---
    SUPADATA_API_KEY: str = ""

    # --- Stripe ---
    STRIPE_PUBLISHABLE_KEY: str = ""
    STRIPE_SECRET_KEY: str = ""
    STRIPE_WEBHOOK_SECRET: str = ""

    # --- BYOP Features ---
    FEATURE_BYOP: bool = False
    FEATURE_BYOP_PUBLISH: bool = False
    BYOP_DEFAULT_REVSHARE_PCT: float = 0.40
    BYOP_PUBLISH_PLATFORMS: str = "youtube,pinterest,reddit,instagram"

    # --- Sharing Kit ---
    SHARE_EMAIL_ENABLED: bool = True
    SHARE_EMAIL_DAILY_LIMIT: int = 200
    SHAREKIT_DEFAULT_HASHTAGS: str = ""

    # --- Logging ---
    LOG_LEVEL: str = "INFO"

    # --- Python runtime ---
    PYTHON_VERSION: str = "3.11"

    # --- Helpers ---
    @property
    def META_BASE(self) -> str:
        return f"https://graph.facebook.com/{self.META_GRAPH_VERSION}"

    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()
