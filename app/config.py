import os
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = "sqlite:///./local.db"
    s3_bucket: str = ""
    s3_access_key_id: str = ""
    s3_secret_access_key: str = ""
    s3_region: str = "us-east-1"
    affil_base_url: str = "https://example.com"
    app_base_url: str = "http://localhost:5000"
    jwt_secret: str = "your-secret-key-here"
    
    # SerpAPI configuration
    SERPAPI_KEY: str = ""
    SERPAPI_HL: str = "fr"
    SERPAPI_GL: str = "FR"
    SERPAPI_CACHE_TTL: int = 3600
    SERPAPI_MAX_RESULTS: int = 10
    
    # Meta / Instagram Graph API
    META_APP_ID: str = ""
    META_APP_SECRET: str = ""
    META_REDIRECT_URL: str = ""
    META_GRAPH_VERSION: str = "v21.0"
    META_SCOPES: str = "pages_show_list,pages_read_engagement,instagram_basic,instagram_content_publish"
    
    # AI Orchestrator / Autopilot
    FEATURE_AUTOPILOT: bool = True
    AI_TICK_INTERVAL_MIN: int = 10
    AI_MAX_ACTIONS_PER_TICK: int = 5
    AI_CONFIDENCE_THRESHOLD: float = 0.55
    AI_DRY_RUN: bool = False
    AI_OBJECTIVE: str = "revenue_ctr_safe"
    AI_LOOKBACK_DAYS: int = 7
    AI_MIN_CTR: float = 0.008
    AI_MIN_QUALITY: float = 0.70
    AI_MAX_RISK: float = 0.20
    
    # Partner Payouts
    PAYOUT_MIN_EUR: float = 10.0
    PAYOUT_METHODS: str = "paypal,bank"
    DEFAULT_EPC_EUR: float = 0.25
    OFFER_MODE: str = "cpc_dynamic"
    CPC_DEFAULT_EUR: float = 0.10
    CPC_MIN_EUR: float = 0.06
    CPC_MAX_EUR: float = 0.12
    REVSHARE_BASE_PCT: float = 0.40
    CPC_SAFETY_MARGIN_EUR: float = 0.05
    
    # Brevo email settings
    BREVO_API_KEY: str = ""
    BASE_URL: str = "http://localhost:5000"
    
    # BYOP Publishing Features
    FEATURE_BYOP_PUBLISH: bool = True
    BYOP_PUBLISH_PLATFORMS: str = "youtube,pinterest,reddit,instagram"
    
    @property
    def META_BASE(self) -> str:
        return f"https://graph.facebook.com/{self.META_GRAPH_VERSION}"
    
    class Config:
        env_file = ".env"


settings = Settings()
