import sys
import os

# Ensure project root is in sys.path so 'from app...' works when Vercel imports app/main.py directly
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, RedirectResponse
from app.core.config import settings
from app.api.routes import router as api_router
from app.api.charter_routes import charter_router

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="Intelligent Freight Forecasting & Vessel Chartering Optimization for SAIL / Ministry of Steel"
)

# Enable CORS for all origins
# NOTE: allow_credentials must be False when allow_origins=["*"]
# Starlette raises AssertionError if both are True simultaneously.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.exception_handler(Exception)
async def custom_global_exception_handler(request, exc):
    import traceback
    err_tb = traceback.format_exc()
    return HTMLResponse(
        content=f"""<!DOCTYPE html>
<html><head><title>System Error</title><style>body{{background:#080808;color:#f87171;font-family:monospace;padding:32px;}}pre{{background:#121418;border:1px solid #334155;padding:16px;border-radius:8px;color:#cbd5e1;overflow:auto;}}</style></head>
<body><h2>FreightWaves Server Exception</h2><pre>{err_tb}</pre></body></html>""",
        status_code=500
    )

@app.middleware("http")
async def vercel_path_rewrite_middleware(request, call_next):
    # When deployed on Vercel, x-matched-path contains the original requested URL (e.g. /sail-portal, /api/v1/optimize)
    matched_path = request.headers.get("x-matched-path") or request.headers.get("x-invoke-path") or request.headers.get("x-forwarded-uri")
    if matched_path:
        clean_path = matched_path.split("?")[0]
        if clean_path and not clean_path.startswith("/api/index"):
            request.scope["path"] = clean_path
    return await call_next(request)

# Include API Routers
app.include_router(api_router, prefix=settings.API_V1_STR)
app.include_router(charter_router, prefix=settings.API_V1_STR)

# Serve Frontend static directory
static_dir = os.path.join(os.path.dirname(__file__), "static")
if os.path.exists(static_dir):
    app.mount("/static", StaticFiles(directory=static_dir), name="static")

@app.get("/", response_class=HTMLResponse)
def serve_home_ui():
    """Main Freight Maritime Landing Page"""
    home_file = os.path.join(os.path.dirname(__file__), "static", "index.html")
    if os.path.exists(home_file):
        with open(home_file, "r", encoding="utf-8") as f:
            return HTMLResponse(content=f.read())
    return HTMLResponse(content="<h1>Freight Maritime Home page not found.</h1>", status_code=404)

@app.get("/sail-portal", response_class=HTMLResponse)
def serve_sail_portal_ui():
    """SAIL & Ministry of Steel Intelligent Charter Decision Workspace"""
    portal_file = os.path.join(os.path.dirname(__file__), "static", "sail_portal.html")
    if os.path.exists(portal_file):
        with open(portal_file, "r", encoding="utf-8") as f:
            return HTMLResponse(content=f.read())
    return HTMLResponse(content="<h1>SAIL Portal workspace page not found.</h1>", status_code=404)

@app.get("/admin", response_class=HTMLResponse)
def serve_admin_ui():
    """FreightWaves Admin Dashboard — Charter Inquiry Management"""
    admin_file = os.path.join(os.path.dirname(__file__), "static", "admin.html")
    if os.path.exists(admin_file):
        with open(admin_file, "r", encoding="utf-8") as f:
            return HTMLResponse(content=f.read())
    return HTMLResponse(content="<h1>Admin dashboard page not found.</h1>", status_code=404)

@app.get("/oris")
def redirect_oris_to_home():
    """Backward-compatibility redirect"""
    return RedirectResponse(url="/", status_code=301)
