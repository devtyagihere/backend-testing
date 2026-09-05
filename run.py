import socket
import uvicorn
import os
from app.core.config import settings

def find_available_port(host: str, starting_port: int) -> int:
    """Find the first available port starting from starting_port."""
    port = starting_port
    while port < starting_port + 50:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.bind((host, port))
                return port
            except OSError:
                port += 1
    return starting_port

if __name__ == "__main__":
    configured_port = int(os.environ.get("PORT", settings.PORT))
    host = os.environ.get("HOST", "0.0.0.0")
    
    port = find_available_port(host, configured_port)
    if port != configured_port:
        print(f"[!] Notice: Port {configured_port} is already in use by another process.")
        print(f"[+] Automatically switched to available port: {port}")
    
    display_host = "localhost" if host == "0.0.0.0" else host
    print("=" * 70)
    print("[SagarAi] INTELLIGENT FREIGHT FORECASTING & CHARTERING ENGINE")
    print(f"[*] Interactive UI:      http://{display_host}:{port}/")
    print(f"[*] SAIL Portal:         http://{display_host}:{port}/sail-portal")
    print(f"[*] Admin Cockpit:       http://{display_host}:{port}/admin")
    print(f"[*] API Documentation:  http://{display_host}:{port}/docs")
    print("=" * 70)
    
    uvicorn.run(
        "app.main:app",
        host=host,
        port=port,
        reload=False
    )
