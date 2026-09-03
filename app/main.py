import os
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
