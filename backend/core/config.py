# core/config.py
from pydantic_settings import BaseSettings
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
    CORS_ORIGINS: str = "http://localhost:3000,http://localhost:5173,http://localhost:5174"

    # ===== engine =====
    # SECURITY FIX: Removed hardcoded internal IP - must be set via environment variable
    ENGINE_URL: str = ""  # Set via ENGINE_URL environment variable
    ENGINE_TIMEOUT: int = 60

    # ===== multi-spot engine =====
    ENABLE_MULTI_SPOT: bool = False
    ENGINE_SPOTS: str = ""  # JSON array of spot configs
    SPOT_REQUEST_TIMEOUT: int = 30
    SPOT_MAX_RETRIES: int = 2

    # ===== database =====
    # SECURITY FIX: Removed hardcoded credentials - must be set via environment variable
    # For Railway: DATABASE_URL is automatically provided
    # For local dev: Set DATABASE_URL in .env file
    DATABASE_URL: str = ""

    # ===== security =====
    # SECURITY FIX: JWT_SECRET_KEY must be set via environment variable
    # Using a weak default only for local development convenience
    JWT_SECRET_KEY: str = "CHANGE_ME_IN_PRODUCTION"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    # ===== email (Resend) =====
    RESEND_API_KEY: str = ""
    RESEND_FROM_EMAIL: str = "noreply@catachess.com"
    VERIFICATION_CODE_EXPIRE_MINUTES: int = 15
    VERIFICATION_CODE_LENGTH: int = 6

    # ===== storage =====
    DATA_ROOT: Path = Path("data")

    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "ignore"

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
