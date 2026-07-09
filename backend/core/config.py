"""
Created at: 2026-07-08 23:15 EDT
Created by: Codex
Last Modified at: 2026-07-08 23:25 EDT
Last Modified by: Codex

Application settings loaded from environment variables.
"""

from pydantic_settings import BaseSettings, SettingsConfigDict
from pathlib import Path
import os
import sys
import re

class Settings(BaseSettings):
    # ===== basic =====
    ENV: str = "dev"
    # SECURITY FIX: DEBUG should default to False for production safety
    DEBUG: bool = False

    # ===== CORS =====
    # Comma-separated list of allowed origins
    # For development: "http://localhost:3000,http://localhost:5173"
    # For production: "https://yourdomain.com"
    CORS_ORIGINS: str = "http://localhost:3000,http://localhost:5173,http://localhost:5174,https://catachess.com,https://www.catachess.com,https://chessortag.org,https://www.chessortag.org"
    # Optional regex for dynamic subdomains (e.g., Cloudflare Pages)
    # Default allows any https origin; tighten in production via env.
    CORS_ORIGIN_REGEX: str = r"^https?://.*$"

    # ===== engine =====
    # SECURITY FIX: Removed hardcoded internal IP - must be set via environment variable
    ENGINE_URL: str = ""  # Set via ENGINE_URL environment variable
    ENGINE_TIMEOUT: int = 60
    ENGINE_DISABLE_CLOUD: bool = False

    # Lichess Cloud Eval
    LICHESS_CLOUD_EVAL_URL: str = "https://lichess.org/api/cloud-eval"

    # ===== engine queue =====
    # Number of concurrent engine workers. Product default is capped at 10 so
    # local Stockfish cannot exhaust the 32-core production server.
    ENGINE_QUEUE_MAX_WORKERS: int = 10
    # Rate limit for /api/engine/analyze endpoint (requests per minute per IP)
    ENGINE_RATE_LIMIT_PER_MINUTE: int = 30

    # ===== local engine workers =====
    STOCKFISH_BINARY_PATH: str = "/usr/games/stockfish"
    STOCKFISH_MAX_WORKERS: int = 10
    STOCKFISH_THREADS_PER_WORKER: int = 1
    STOCKFISH_HASH_MB: int = 64
    STOCKFISH_MAX_DEPTH: int = 24
    STOCKFISH_MAX_MULTIPV: int = 5
    ENGINE_SLOT_LOCK_DIR: str = "/tmp/catachess_engine_slots"
    ALPHAZERO_COMMAND: str = ""
    ALPHAZERO_MODEL_PATH: str = ""
    ALPHAZERO_MAX_WORKERS: int = 1
    ALPHAZERO_TIMEOUT: int = 60
    ALPHAZERO_CUDA_VISIBLE_DEVICES: str = "0"
    LC0_BINARY_PATH: str = "/usr/games/lc0"
    LC0_WEIGHTS_PATH: str = ""
    LC0_BACKEND: str = "onnx-rocm"
    LC0_MAX_WORKERS: int = 1
    LC0_TIMEOUT: int = 60
    LC0_NODES_PER_DEPTH: int = 64
    LC0_MAX_NODES: int = 1600
    LC0_MAX_MULTIPV: int = 5

    # ===== human move predictors =====
    PREDICTOR_RATE_LIMIT_PER_MINUTE: int = 20
    MAIA_PYTHON: str = "/home/catadragon/.venv/bin/python"
    MAIA_SCRIPT_PATH: str = "/home/catadragon/Code/transformer_chess/other_model/use/maia2_position_infer.py"
    MAIA_MODEL_TYPE: str = "rapid"
    MAIA_DEVICE: str = "cpu"
    MAIA_MAX_WORKERS: int = 2
    MAIA_TIMEOUT: int = 30
    CATIE_MODEL_BASE_URL: str = "http://127.0.0.1:8000"
    CATIE_MODEL_ID: str = "carlsen.best"
    CATIE_DEFAULT_ELO: int = 1500
    CATIE_POLL_TIMEOUT: int = 20
    CATIE_POLL_INTERVAL_SECONDS: float = 0.5

    # ===== multi-spot engine =====
    ENABLE_MULTI_SPOT: bool = False
    ENGINE_SPOTS: str = ""  # JSON array of spot configs
    SPOT_REQUEST_TIMEOUT: int = 30
    SPOT_MAX_RETRIES: int = 2
    ENGINE_FALLBACK_MODE: str = "legal"  # "legal" for local rule-based fallback, "off" to disable

    # ===== PGN v2 Feature Flag =====
    PGN_V2_ENABLED: bool = False

    # ===== database =====
    # SECURITY FIX: Removed hardcoded credentials - must be set via environment variable
    # For Railway: DATABASE_URL is automatically provided
    # For local dev: Set DATABASE_URL in .env file
    DATABASE_URL: str = ""
    # Tagger-specific database (separate from workspace DB)
    TAGGER_DATABASE_URL: str = ""

    # Database connection pool configuration
    DB_POOL_SIZE: int = 20              # Base connection pool size
    DB_MAX_OVERFLOW: int = 40           # Additional connections when pool is exhausted
    DB_POOL_RECYCLE: int = 3600         # Recycle connections after seconds (1 hour)
    DB_POOL_TIMEOUT: int = 30           # Connection acquisition timeout in seconds

    # ===== MongoDB (Engine Cache) =====
    # Railway provides both MONGO_URL (internal) and MONGO_PUBLIC_URL (public)
    # Use MONGO_URL for Railway deployments (faster, internal network)
    MONGO_URL: str = ""
    MONGODB_DATABASE: str = "catachess"
    MONGODB_CACHE_COLLECTION: str = "engine_cache"
    # NOTE: Data is stored PERMANENTLY (no auto-expiration)
    # Use cleanup_cold_positions() method if manual cleanup is needed

    # ===== security =====
    # SECURITY FIX: JWT_SECRET_KEY must be set via environment variable
    # Using a weak default only for local development convenience
    JWT_SECRET_KEY: str = "CHANGE_ME_IN_PRODUCTION"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 30

    # ===== internal worker auth =====
    WORKER_API_TOKEN: str = ""

    # ===== background jobs =====
    ENABLE_PRESENCE_CLEANUP: bool = False

    # ===== email (Resend) =====
    RESEND_API_KEY: str = ""
    RESEND_FROM_EMAIL: str = "noreply@catachess.com"
    VERIFICATION_CODE_EXPIRE_MINUTES: int = 15
    VERIFICATION_CODE_LENGTH: int = 6

    # ===== storage =====
    DATA_ROOT: Path = Path("data")

    model_config = SettingsConfigDict(
        env_file=None if os.getenv("ENV") == "production" else ".env",
        case_sensitive=True,
        extra="ignore",
    )

    @property
    def cors_origins_list(self) -> list[str]:
        """Parse CORS_ORIGINS string into list of origins."""
        if not self.CORS_ORIGINS:
            return []
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",") if origin.strip()]

    def validate_database_url(self):
        """Validate DATABASE_URL has actual values, not placeholders"""
        url = self.DATABASE_URL
        allow_startup = bool(
            os.getenv("ALLOW_CONFIG_WARNINGS")
            or os.getenv("RAILWAY_ENVIRONMENT")
            or os.getenv("RAILWAY_PROJECT_ID")
        )

        if not url:
            print(f"\n{'='*60}")
            print("ERROR: DATABASE_URL is not set!")
            print(f"{'='*60}")
            print("Please set DATABASE_URL in environment variables or .env file.")
            print("\nFor Railway PostgreSQL:")
            print("  1. Add PostgreSQL plugin in Railway dashboard")
            print("  2. Railway will auto-provide DATABASE_URL variable")
            print("\nFor local development:")
            print("  Set DATABASE_URL in .env file:")
            print("  DATABASE_URL=postgresql://user:pass@localhost:5432/dbname")
            print(f"{'='*60}\n")
            if not allow_startup:
                sys.exit(1)
            return

        # Check for common placeholder patterns
        placeholder_patterns = [
            r':port/',  # :port/database
            r'@host:',  # @host:port
            r'//user:',  # //user:password
            r':password@',  # user:password@host
        ]

        for pattern in placeholder_patterns:
            if re.search(pattern, url, re.IGNORECASE):
                print(f"\n{'='*60}")
                print("ERROR: DATABASE_URL contains placeholder values!")
                print(f"{'='*60}")
                print(f"Current DATABASE_URL: {url}")
                print("\nPlease set a valid DATABASE_URL in environment variables.")
                print(f"{'='*60}\n")
                if not allow_startup:
                    sys.exit(1)
                return

    def validate_security_settings(self):
        """Validate security-critical settings are properly configured"""
        warnings = []
        allow_startup = bool(
            os.getenv("ALLOW_CONFIG_WARNINGS")
            or os.getenv("RAILWAY_ENVIRONMENT")
            or os.getenv("RAILWAY_PROJECT_ID")
        )

        # Check JWT secret key
        if self.JWT_SECRET_KEY in ["CHANGE_ME_IN_PRODUCTION", "dev-secret-key-change-in-production", ""]:
            warnings.append("⚠️  JWT_SECRET_KEY is using default/weak value! Set a strong secret in production.")

        # Check ENGINE_URL
        if not self.ENGINE_URL and self.ENV == "production":
            warnings.append("⚠️  ENGINE_URL is not set!")

        # Check DEBUG in production
        if self.DEBUG and self.ENV == "production":
            warnings.append("⚠️  DEBUG=True in production environment! This exposes sensitive information.")

        if warnings:
            print(f"\n{'='*60}")
            print("SECURITY WARNINGS:")
            print(f"{'='*60}")
            for warning in warnings:
                print(warning)
            print(f"{'='*60}\n")

            # In production, fail fast on security issues unless explicitly allowed.
            if self.ENV == "production" and not allow_startup:
                print("ERROR: Cannot start in production with security warnings!")
                sys.exit(1)


settings = Settings()
settings.validate_database_url()
settings.validate_security_settings()
