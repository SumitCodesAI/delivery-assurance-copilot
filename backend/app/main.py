"""
FastAPI main application entry point.
"""

import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.db.session import create_all_tables
from app.api import upload, extract, review, export, auth


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager for app startup and shutdown.
    """
    # Startup
    print("Starting Delivery Assurance Copilot API...")
    await create_all_tables()
    print("Database tables created/verified")
    
    # Create Jira addon tables if enabled
    if os.getenv("JIRA_ADDON_ENABLED", "false").lower() == "true":
        try:
            from app.addons.jira_addon.models import Base as JiraBase
            from app.db.session import engine
            async with engine.begin() as conn:
                await conn.run_sync(JiraBase.metadata.create_all)
            print("Jira addon tables created/verified")
        except Exception as e:
            print(f"Warning: Failed to create Jira addon tables: {e}")

    yield

    # Shutdown
    print("Shutting down Delivery Assurance Copilot API...")


# Create FastAPI app
app = FastAPI(
    title="Delivery Assurance Copilot API",
    version="1.0.0",
    description="AI-powered requirements to test generation and delivery assurance platform",
    lifespan=lifespan,
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for now
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router, tags=["Authentication"])
app.include_router(upload.router, prefix="/api/v1", tags=["Upload & Projects"])
app.include_router(extract.router, prefix="/api/v1", tags=["Pipeline"])
app.include_router(review.router, prefix="/api/v1", tags=["Review"])
app.include_router(export.router, prefix="/api/v1", tags=["Export"])

# Include Jira addon router if enabled
if os.getenv("JIRA_ADDON_ENABLED", "false").lower() == "true":
    try:
        from app.addons.jira_addon.router import router as jira_router
        app.include_router(jira_router)
        print("✓ Jira addon enabled")
    except Exception as e:
        print(f"⚠ Warning: Failed to load Jira addon: {e}")


# Health check endpoint
@app.get("/health", tags=["Health"])
async def health_check() -> dict:
    """
    Health check endpoint.

    Returns:
        Health status
    """
    return {
        "status": "healthy",
        "service": "Delivery Assurance Copilot API",
        "version": "1.0.0",
    }


@app.get("/", tags=["Root"])
async def root() -> dict:
    """
    Root endpoint with API information.

    Returns:
        API information
    """
    return {
        "name": "Delivery Assurance Copilot API",
        "version": "1.0.0",
        "docs": "/docs",
        "openapi": "/openapi.json",
    }
