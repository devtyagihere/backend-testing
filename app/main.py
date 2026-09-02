import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, RedirectResponse
from app.core.config import settings
from app.api.routes import router as api_router
from app.api.charter_routes import charter_router

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="Intelligent Freight Forecasting & Vessel Chartering Optimization for SAIL / Ministry of Steel"
)

# Enable CORS for all origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
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

@app.get("/")
def serve_home_ui():
    """Main Freight Maritime Landing Page"""
    home_file = os.path.join(os.path.dirname(__file__), "static", "index.html")
    if os.path.exists(home_file):
        return FileResponse(home_file)
    return {"message": "Freight Maritime Home page not found."}

@app.get("/sail-portal")
def serve_sail_portal_ui():
    """SAIL & Ministry of Steel Intelligent Charter Decision Workspace"""
    portal_file = os.path.join(os.path.dirname(__file__), "static", "sail_portal.html")
    if os.path.exists(portal_file):
        return FileResponse(portal_file)
    return {"message": "SAIL Portal workspace page not found."}

@app.get("/admin")
def serve_admin_ui():
    """FreightWaves Admin Dashboard — Charter Inquiry Management"""
    admin_file = os.path.join(os.path.dirname(__file__), "static", "admin.html")
    if os.path.exists(admin_file):
        return FileResponse(admin_file)
    return {"message": "Admin dashboard page not found."}

@app.get("/oris")
def redirect_oris_to_home():
    """Backward-compatibility redirect"""
    return RedirectResponse(url="/", status_code=301)
