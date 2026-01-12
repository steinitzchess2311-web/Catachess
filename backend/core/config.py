# core/config.py
from pydantic_settings import BaseSettings
from pathlib import Path
import os
import sys
import re

class Settings(BaseSettings):
    # ===== basic =====
    ENV: str = "dev"
    DEBUG: bool = True

    # ===== engine =====
    ENGINE_URL: str = "http://192.168.40.33:8001"
    ENGINE_TIMEOUT: int = 60

    # ===== multi-spot engine =====
    ENABLE_MULTI_SPOT: bool = False
    ENGINE_SPOTS: str = ""  # JSON array of spot configs
    SPOT_REQUEST_TIMEOUT: int = 30
    SPOT_MAX_RETRIES: int = 2

    # ===== database =====
    # Default to Railway external proxy for local development
    # Change to postgres.railway.internal:5432 for production deployment
    DATABASE_URL: str = "postgresql://postgres:yRuedDjiwzhbrBKDbIDCtCxTMzzRDQTL@yamabiko.proxy.rlwy.net:20407/railway"

    # ===== security =====
    JWT_SECRET_KEY: str = "dev-secret-key-change-in-production"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    # ===== email (Resend) =====
    RESEND_API_KEY: str = "re_eRozq9hQ_NF7t1opa4d3AwUwzfZXj9VGy"
    RESEND_FROM_EMAIL: str = "noreply@catachess.com"
    VERIFICATION_CODE_EXPIRE_MINUTES: int = 15
    VERIFICATION_CODE_LENGTH: int = 6

    # ===== storage =====
    DATA_ROOT: Path = Path("data")

    class Config:
        env_file = ".env"
        case_sensitive = True

    def validate_database_url(self):
        """Validate DATABASE_URL has actual values, not placeholders"""
        url = self.DATABASE_URL

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
                print("\nPlease set a valid DATABASE_URL in Railway environment variables.")
                print("\nFor Railway PostgreSQL:")
                print("  1. Add PostgreSQL plugin in Railway dashboard")
                print("  2. Railway will auto-provide DATABASE_URL variable")
                print("  3. Or manually set: postgresql://user:pass@host:port/dbname")
                print(f"{'='*60}\n")
                sys.exit(1)


settings = Settings()
settings.validate_database_url()

