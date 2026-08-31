import os
from pydantic import BaseModel

class Settings(BaseModel):
    PROJECT_NAME: str = "SAIL Intelligent Freight Forecasting & Chartering System"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    PORT: int = int(os.getenv("PORT", 8000))
    HOST: str = os.getenv("HOST", "0.0.0.0")
    DEBUG: bool = os.getenv("DEBUG", "True").lower() == "true"
    CORS_ORIGINS: list[str] = ["*"]

settings = Settings()
