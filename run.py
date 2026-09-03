import uvicorn
import os
from app.core.config import settings

if __name__ == "__main__":
    port = int(os.environ.get("PORT", settings.PORT))
    host = os.environ.get("HOST", "0.0.0.0")
    print("=" * 70)
    print("[SAIL] INTELLIGENT FREIGHT FORECASTING & CHARTERING ENGINE")
    print(f"[*] Server starting at: http://{host}:{port}")
    print(f"[*] Interactive UI:      http://{host}:{port}/")
    print(f"[*] API Documentation:  http://{host}:{port}/docs")
    print("=" * 70)
    uvicorn.run(
        "app.main:app",
        host=host,
        port=port,
        reload=False
    )
