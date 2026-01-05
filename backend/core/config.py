# core/config.py
from pydantic_settings import BaseSettings
from pathlib import Path
import os

class Settings(BaseSettings):
    # ===== basic =====
    ENV: str = "dev"
    DEBUG: bool = True

    # ===== engine =====
    ENGINE_URL: str = "http://192.168.40.33:8001"
    ENGINE_TIMEOUT: int = 60

    # ===== database =====
    DATABASE_URL: str = "postgresql://postgres:yRuedDjiwzhbrBKDbIDCtCxTMzzRDQTL@yamabiko.proxy.rlwy.net:20407/railway"

    # ===== security =====
    JWT_SECRET_KEY: str = "dev-secret-key-change-in-production"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    # ===== storage =====
    DATA_ROOT: Path = Path("data")

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()

