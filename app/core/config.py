import os
from typing import Optional
from dotenv import load_dotenv
from pydantic import BaseModel

# Load environment variables from .env file
load_dotenv()

class Settings(BaseModel):
    PROJECT_NAME: str = "SAIL Intelligent Freight Forecasting & Chartering System"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    PORT: int = int(os.getenv("PORT", 8000))
    HOST: str = os.getenv("HOST", "0.0.0.0")
    DEBUG: bool = os.getenv("DEBUG", "True").lower() == "true"
    CORS_ORIGINS: list[str] = ["*"]

    # Groq AI Settings
    GROQ_API_KEY: Optional[str] = os.getenv("GROQ_API_KEY")
    GROQ_MODEL: str = os.getenv("GROQ_MODEL", "qwen/qwen3.8-27b")

    # Data Pipeline API Keys
    EIA_API_KEY: Optional[str] = os.getenv("EIA_API_KEY")
    ALPHA_VANTAGE_API_KEY: Optional[str] = os.getenv("ALPHA_VANTAGE_API_KEY")
    FRED_API_KEY: Optional[str] = os.getenv("FRED_API_KEY")

    # Supabase — Charter Inquiries
    SUPABASE_URL: Optional[str] = os.getenv("SUPABASE_URL")
    SUPABASE_PUBLISHABLE_KEY: Optional[str] = os.getenv("SUPABASE_PUBLISHABLE_KEY")
    SUPABASE_SERVICE_KEY: Optional[str] = os.getenv("SUPABASE_SERVICE_KEY")

    # Resend — Transactional Email
    RESEND_API_KEY: Optional[str] = os.getenv("RESEND_API_KEY")
    OWNER_EMAIL: str = os.getenv("OWNER_EMAIL", "admin@freightmaritime.com")

    # Admin Dashboard
    ADMIN_SECRET_TOKEN: str = os.getenv("ADMIN_SECRET_TOKEN", "fw-admin-2026-secure-token")

    # Deployment base URL (used in email links — set this in Vercel env vars)
    APP_BASE_URL: str = os.getenv("APP_BASE_URL", "http://localhost:8000")

settings = Settings()
