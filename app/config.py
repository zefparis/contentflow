🛠 Mission Windsurf — Réparer les assets (CSS/JS) du frontend
🎯 Objectif

La page s’affiche “sans style” → les assets Vite (CSS/JS) ne sont pas servis correctement.
Corriger la chaîne build/serve pour que index.html charge bien /assets/*.css et /assets/*.js avec les bons Content-Type.

✅ À faire (ordre strict)
1) vite.config.ts (racine)

Forcer une build canon Vite → dist/public, assets sous /assets :

import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  base: '/',                 // assets résolus en /assets/...
  root: './client',          // si index.html est dans client/
  build: {
    outDir: '../dist/public', // output final
    assetsDir: 'assets',
    emptyOutDir: true,
  },
  plugins: [react()],
})

2) client/src/main.tsx

S’assurer que le CSS est importé :

import './index.css'

3) app/main.py

a) MIME types (avant mounting) :

import mimetypes
mimetypes.add_type("text/css", ".css")
mimetypes.add_type("application/javascript", ".js")


b) Endpoint de debug (rapide pour inspecter le build) :

from fastapi.responses import JSONResponse
from pathlib import Path

@app.get("/__static_debug", include_in_schema=False)
def __static_debug():
    roots = ["app/static", "client/dist/public", "dist/public", "dist", "public"]
    found = []
    for r in roots:
        p = Path(r)
        if p.exists():
            assets = []
            adir = p / "assets"
            if adir.exists():
                assets = [str(x.relative_to(p)) for x in adir.glob("*")][:50]
            found.append({"root": r, "exists": True, "assets_sample": assets})
        else:
            found.append({"root": r, "exists": False})
    return JSONResponse({"roots": found})


c) SPAFallbackMiddleware → ajouter /readyz dans les exclusions si pas déjà :

self.excluded_prefixes = [
    "/api", "/docs", "/redoc", "/openapi.json",
    "/static", "/assets", "/health", "/healthz", "/readyz", "/__feature_flags",
]


d) Mount explicite des assets (belt & suspenders) :

from fastapi.staticfiles import StaticFiles

# si pas déjà fait :
app.mount("/assets", StaticFiles(directory="app/static/assets"), name="assets")


Garder aussi le mount racine app.mount("/", StaticFiles(directory="app/static", html=True), name="static-root") après health & middlewares.

4) Dockerfile (vérifier la copie du build)

Le stage frontend copie /app/dist/public/ → app/static/. Si besoin, ré-assert :

# (déjà en place normalement)
COPY --from=frontend /app/dist/public/ ./app/static/

5) Nettoyage caches (optionnel mais recommandé)

Supprimer les sorties dist/ locales obsolètes avant rebuild (Vite emptyOutDir: true le fait).

Rebuild image et redeploy.

🧪 Tests à exécuter

Debug assets

GET /__static_debug


Attendu: app/static existe et assets_sample contient au moins un index-*.css et index-*.js.

Types

GET /assets/<ton-css>.css → 200 + header Content-Type: text/css

GET /assets/<ton-js>.js → 200 + header Content-Type: application/javascript

Page

GET / → page stylée (pas de 404 dans l’onglet Réseau sur CSS/JS).

Health

GET /healthz = 200

GET /readyz = 200 quand prêt (si activé)

✅ Critères d’acceptation

Plus de rendu “sans style”.

/__static_debug liste les assets sous app/static/assets.

CSS/JS servis avec bons mimetypes.

Aucun 404 sur /assets/* en console navigateur.

🧾 COMPTE RENDU attendu (obligatoire, Markdown)

Résumé exéc’ (≤10 lignes) — ce qui a été modifié et résultat final (page stylée).

Actions appliquées (liste ordonnée + chemins).

Diffs/Extraits clés :

vite.config.ts (bloc complet)

client/src/main.tsx (import CSS)

app/main.py (mimetypes + __static_debug + exclusions + mount /assets)

(optionnel) Dockerfile (ligne COPY)

Preuves :

Sortie /__static_debug

Headers des requêtes /assets/*.css et /assets/*.js

Capture/log de la page chargée avec styles

Points ouverts / TODO :

Si bundle > 500 kB, proposer code-splitting (Vite manualChunks)

CDN/Cache-Control à activer plus tard si besoin

➡️ Applique ces patchs, rebuild, teste, puis livre le compte rendu.# app/config.py
from __future__ import annotations

from typing import Any, List, get_origin

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic_settings.sources import EnvSettingsSource


class _SmartEnvSource(EnvSettingsSource):
    """
    Source ENV custom pour Pydantic Settings v2 :
    - JSON standard: on laisse super().decode_complex_value gérer
    - Fallback CSV: "a,b,c" -> ["a","b","c"] pour list[str]
    - String vide "" pour list[str] -> []
    """

    def decode_complex_value(self, field_name, field, value):  # noqa: N802
        try:
            return super().decode_complex_value(field_name, field, value)
        except Exception:
            # Normalisation fallback
            if isinstance(value, (bytes, bytearray)):
                value = value.decode()
            if isinstance(value, str):
                s = value.strip()
                # list[...] + "" => []
                if get_origin(getattr(field, "annotation", None)) is list and s == "":
                    return []
                # CSV => liste
                if ("," in s) and not s.startswith(("{", "[")):
                    return [x.strip() for x in s.split(",") if x.strip()]
            # Sinon, on relance l'erreur d'origine
            raise


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
    PORT: int = 8000

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
    PAYOUT_METHODS: List[str] = ["paypal", "bank"]

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
    AFF_ALLOWLIST_IPS: List[str] = []

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
    BYOP_PUBLISH_PLATFORMS: List[str] = ["youtube", "pinterest", "reddit", "instagram"]

    # --- Sharing Kit ---
    SHARE_EMAIL_ENABLED: bool = True
    SHARE_EMAIL_DAILY_LIMIT: int = 200
    SHAREKIT_DEFAULT_HASHTAGS: str = ""

    # --- Logging ---
    LOG_LEVEL: str = "INFO"

    # --- CORS ---
    CORS_ORIGINS: List[str] = ["*"]

    # Pydantic Settings v2
    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=False,
    )

    # ⚠️ v2: signature avec settings_cls en 1er
    @classmethod
    def settings_customise_sources(  # type: ignore[override]
        cls,
        settings_cls,            # <- requis en v2
        init_settings,
        env_settings,
        dotenv_settings,
        file_secret_settings,
    ):
        # Remplace la source ENV par notre source tolérante CSV/JSON/empty
        return (init_settings, _SmartEnvSource(settings_cls), dotenv_settings, file_secret_settings)

    # Filet de sécu au cas où une string brute passe encore
    @field_validator(
        "PAYOUT_METHODS",
        "BYOP_PUBLISH_PLATFORMS",
        "AFF_ALLOWLIST_IPS",
        "CORS_ORIGINS",
        mode="before",
    )
    @classmethod
    def _split_csv(cls, v):
        if isinstance(v, list):
            return v
        if v is None or v == "":
            return []
        if isinstance(v, str):
            return [s.strip() for s in v.split(",") if s.strip()]
        return v


settings = Settings()
