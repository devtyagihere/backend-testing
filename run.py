import uvicorn
import os
from app.core.config import settings

if __name__ == "__main__":
    print("=" * 70)
    print("[SAIL] INTELLIGENT FREIGHT FORECASTING & CHARTERING ENGINE")
    print(f"[*] Server starting at: http://localhost:{settings.PORT}")
    print(f"[*] Interactive UI:      http://localhost:{settings.PORT}/")
    print(f"[*] API Documentation:  http://localhost:{settings.PORT}/docs")
    print("=" * 70)
    uvicorn.run(
        "app.main:app",
        host="127.0.0.1",
        port=settings.PORT,
        reload=False
    )
