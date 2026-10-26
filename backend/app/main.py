import os
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.core.database import Base, engine
from app.api import (
    auth, leads, imports, exports, discovery, audits,
    enrichment, scoring, outreach, campaigns, tasks,
    suppression, dashboard, settings_api, health
)

# Create all tables on startup if they don't exist
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title=settings.APP_NAME,
    description="LeadGen Lite — B2B Lead Finder, Excel Importer, SEO Auditor, Scorer, and CRM",
    version="1.0.0",
    openapi_url=f"{settings.API_V1_STR}/openapi.json"
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register All API Endpoints
app.include_router(health.router, prefix=settings.API_V1_STR)
app.include_router(auth.router, prefix=settings.API_V1_STR)
app.include_router(leads.router, prefix=settings.API_V1_STR)
app.include_router(imports.router, prefix=settings.API_V1_STR)
app.include_router(exports.router, prefix=settings.API_V1_STR)
app.include_router(discovery.router, prefix=settings.API_V1_STR)
app.include_router(audits.router, prefix=settings.API_V1_STR)
app.include_router(enrichment.router, prefix=settings.API_V1_STR)
app.include_router(scoring.router, prefix=settings.API_V1_STR)
app.include_router(outreach.router, prefix=settings.API_V1_STR)
app.include_router(campaigns.router, prefix=settings.API_V1_STR)
app.include_router(tasks.router, prefix=settings.API_V1_STR)
app.include_router(suppression.router, prefix=settings.API_V1_STR)
app.include_router(dashboard.router, prefix=settings.API_V1_STR)
app.include_router(settings_api.router, prefix=settings.API_V1_STR)


# Serve compiled React frontend assets if built
frontend_dist = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../frontend/dist"))
assets_dir = os.path.join(frontend_dist, "assets")

if os.path.exists(assets_dir):
    app.mount("/assets", StaticFiles(directory=assets_dir), name="assets")

@app.get("/")
def serve_root():
    index_file = os.path.join(frontend_dist, "index.html")
    if os.path.exists(index_file):
        return FileResponse(index_file)
    return {
        "message": "Welcome to LeadGen Lite API",
        "docs": "/docs",
        "health": f"{settings.API_V1_STR}/health"
    }

@app.get("/{full_path:path}")
def serve_spa(full_path: str):
    index_file = os.path.join(frontend_dist, "index.html")
    if os.path.exists(index_file) and not full_path.startswith("api"):
        return FileResponse(index_file)
    return {
        "message": "Welcome to LeadGen Lite API",
        "docs": "/docs",
        "health": f"{settings.API_V1_STR}/health"
    }

