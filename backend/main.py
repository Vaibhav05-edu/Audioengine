"""
Audio-Only Drama — Automated FX Engine
FastAPI backend application
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
import uvicorn
import os
from pathlib import Path
from datetime import datetime

from .config import settings
from .database import create_tables
from .api.v1.api import api_router

# Create FastAPI app
app = FastAPI(
    title=settings.app_name,
    description="""
    ## Audio Drama FX Engine API
    
    A comprehensive API for automated audio processing and effects generation for audio dramas.
    
    ### Key Features
    
    * **Scene Management**: Create and manage audio drama scenes with timeline JSON
    * **Asset Ingestion**: Upload and manage audio assets (dialogue, music, SFX, ambience)
    * **FX Planning**: Plan and configure audio effects for scenes
    * **FX Generation**: Generate audio effects based on scene configuration
    * **Render Stems**: Render separate audio stems for final mixing
    * **Download Management**: Download processed audio files
    
    ### Workflow
    
    1. **Ingest Assets**: Upload audio files to scenes using `/workflow/ingest`
    2. **Plan FX**: Create FX plans for scenes using `/workflow/plan_fx`
    3. **Generate FX**: Process FX plans using `/workflow/gen_fx`
    4. **Render Stems**: Render audio stems using `/workflow/render_stems`
    5. **Download**: Download rendered files using `/workflow/download`
    
    ### Timeline JSON Format
    
    Scenes store timeline information in a structured JSON format:
    
    ```json
    {
      "version": "1.0",
      "duration": 120.0,
      "sample_rate": 44100,
      "tracks": [
        {
          "name": "Dialogue Track",
          "type": "dialogue",
          "assets": [...],
          "volume": 1.0,
          "pan": 0.0,
          "mute": false,
          "solo": false
        }
      ],
      "metadata": {}
    }
    ```
    """,
    version=settings.app_version,
    docs_url="/docs" if settings.debug else None,
    redoc_url="/redoc" if settings.debug else None,
    openapi_tags=[
        {
            "name": "projects",
            "description": "Project management operations"
        },
        {
            "name": "scenes",
            "description": "Scene management operations"
        },
        {
            "name": "fx-plans",
            "description": "FX plan management operations"
        },
        {
            "name": "assets",
            "description": "Asset management operations"
        },
        {
            "name": "renders",
            "description": "Render management operations"
        },
        {
            "name": "workflow",
            "description": "Main workflow operations (ingest, plan_fx, gen_fx, render_stems, download)"
        },
        {
            "name": "audio",
            "description": "Audio processing operations"
        },
        {
            "name": "screenplay",
            "description": "Screenplay parsing and scene extraction operations"
        },
        {
            "name": "alignment",
            "description": "Audio alignment and word-level timestamp operations"
        },
        {
            "name": "sfx",
            "description": "SFX and ambience generation using ElevenLabs"
        },
        {
            "name": "prompt-generation",
            "description": "Automatic prompt generation from scene analysis"
        }
    ]
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API router
app.include_router(api_router, prefix=settings.api_v1_prefix)

# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "audio-drama-fx-engine",
        "timestamp": datetime.utcnow(),
        "version": settings.app_version,
        "environment": settings.environment
    }

# Root endpoint
@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Audio-Only Drama — Automated FX Engine",
        "version": settings.app_version,
        "docs": "/docs" if settings.debug else None,
        "health": "/health",
        "api": settings.api_v1_prefix
    }

# API status endpoint
@app.get("/api/status")
async def api_status():
    """API status endpoint"""
    return {
        "api_version": "v1",
        "status": "operational",
        "features": {
            "audio_processing": True,
            "effects_engine": True,
            "whisperx_integration": True,
            "real_time_processing": False
        },
        "environment": settings.environment
    }

# Error handlers
@app.exception_handler(404)
async def not_found_handler(request, exc):
    return JSONResponse(
        status_code=404,
        content={"error": "Not found", "message": "The requested resource was not found"}
    )

@app.exception_handler(500)
async def internal_error_handler(request, exc):
    return JSONResponse(
        status_code=500,
        content={"error": "Internal server error", "message": "An unexpected error occurred"}
    )

# Startup event
@app.on_event("startup")
async def startup_event():
    """Initialize application on startup"""
    # Create database tables
    create_tables()
    
    # Create necessary directories
    Path(settings.upload_dir).mkdir(parents=True, exist_ok=True)
    Path(settings.temp_dir).mkdir(parents=True, exist_ok=True)

if __name__ == "__main__":
    # Get configuration from environment variables
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", 8000))
    debug = os.getenv("DEBUG", "false").lower() == "true"
    reload = os.getenv("AUTO_RELOAD", "true").lower() == "true"
    
    print(f"🚀 Starting Audio Drama FX Engine server...")
    print(f"📍 Server will be available at: http://{host}:{port}")
    print(f"📚 API documentation: http://{host}:{port}/docs")
    print(f"🔍 Health check: http://{host}:{port}/health")
    
    uvicorn.run(
        "main:app",
        host=host,
        port=port,
        reload=reload,
        log_level="info" if not debug else "debug"
    )
