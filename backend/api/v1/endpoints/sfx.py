"""
SFX generation API endpoints
"""

from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field

from ....database import get_db
from ....models import Scene, Asset, User
from ....services.elevenlabs_sfx import ElevenLabsSFXClient, SFXGenerationRequest
from ....tasks.sfx_tasks import generate_sfx_task, generate_ambience_task, clear_sfx_cache_task
from ...dependencies import get_current_active_user

router = APIRouter()


class SFXGenerationRequestModel(BaseModel):
    """Request model for SFX generation"""
    prompt: str = Field(..., min_length=1, max_length=500, description="Text prompt for SFX generation")
    duration: float = Field(..., ge=1.0, le=300.0, description="Duration in seconds (1-300)")
    seed: Optional[int] = Field(None, ge=0, le=2147483647, description="Fixed seed for deterministic generation")
    loopable: bool = Field(default=False, description="Whether to generate loopable ambience")
    crossfade_duration: float = Field(default=0.5, ge=0.1, le=5.0, description="Crossfade duration in seconds")
    scene_id: Optional[int] = Field(None, description="Scene ID to associate with generated asset")
    asset_name: Optional[str] = Field(None, max_length=255, description="Name for the generated asset")
    async_processing: bool = Field(default=True, description="Process asynchronously")


class SFXGenerationResponse(BaseModel):
    """Response model for SFX generation"""
    success: bool
    message: str
    task_id: Optional[str] = None
    result: Optional[Dict[str, Any]] = None


class AmbienceGenerationRequestModel(BaseModel):
    """Request model for ambience generation"""
    prompt: str = Field(..., min_length=1, max_length=500, description="Text prompt for ambience generation")
    duration: float = Field(..., ge=1.0, le=300.0, description="Duration in seconds (1-300)")
    seed: Optional[int] = Field(None, ge=0, le=2147483647, description="Fixed seed for deterministic generation")
    crossfade_duration: float = Field(default=1.0, ge=0.1, le=5.0, description="Crossfade duration for seamless looping")
    scene_id: Optional[int] = Field(None, description="Scene ID to associate with generated asset")
    asset_name: Optional[str] = Field(None, max_length=255, description="Name for the generated asset")
    async_processing: bool = Field(default=True, description="Process asynchronously")


class SFXStatusResponse(BaseModel):
    """Response model for SFX generation status"""
    task_id: str
    status: str
    progress: Optional[Dict[str, Any]] = None
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


class SFXCacheInfoResponse(BaseModel):
    """Response model for SFX cache information"""
    cache_dir: str
    total_files: int
    total_size_bytes: int
    total_size_mb: float


@router.post("/generate", response_model=SFXGenerationResponse)
def generate_sfx(
    request: SFXGenerationRequestModel,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Generate SFX audio from text prompt using ElevenLabs
    
    This endpoint generates sound effects from text prompts using ElevenLabs' SFX API.
    It supports tiling for longer durations, loopable ambience, and deterministic generation.
    
    **Generation Features:**
    - Text-to-sound generation using ElevenLabs API
    - Automatic tiling for durations > 22 seconds
    - Crossfade stitching for seamless audio
    - Loopable ambience generation
    - Fixed seeds for deterministic results
    - High-quality output: 48kHz/24-bit WAV
    
    **Tiling System:**
    For durations longer than ~22 seconds, the system automatically:
    1. Splits the request into multiple tiles
    2. Generates each tile separately
    3. Stitches tiles together with crossfades
    4. Ensures seamless audio continuity
    
    **Loopable Ambience:**
    When `loopable=true`, the generated audio is optimized for seamless looping:
    - Crossfade applied to start/end of audio
    - Seamless loop points created
    - Perfect for background ambience
    
    Args:
        request: SFX generation request parameters
        background_tasks: FastAPI background tasks
        db: Database session
        current_user: Current authenticated user
    
    Returns:
        Generation response with task ID or results
    
    Raises:
        HTTPException: 404 if scene not found, 400 if generation fails
    """
    # Verify scene exists if provided
    if request.scene_id:
        scene = db.query(Scene).filter(Scene.id == request.scene_id).first()
        if not scene:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Scene not found"
            )
    
    try:
        if request.async_processing:
            # Process asynchronously
            task = generate_sfx_task.delay(
                prompt=request.prompt,
                duration=request.duration,
                seed=request.seed,
                loopable=request.loopable,
                crossfade_duration=request.crossfade_duration,
                scene_id=request.scene_id,
                asset_name=request.asset_name
            )
            
            message = f"Started SFX generation: {request.prompt[:50]}..."
            if request.loopable:
                message += " (loopable ambience)"
            
            return SFXGenerationResponse(
                success=True,
                message=message,
                task_id=task.id
            )
        
        else:
            # Process synchronously
            sfx_client = ElevenLabsSFXClient()
            
            # Create generation request
            generation_request = SFXGenerationRequest(
                prompt=request.prompt,
                duration=request.duration,
                seed=request.seed,
                loopable=request.loopable,
                crossfade_duration=request.crossfade_duration,
                output_format="wav",
                sample_rate=48000,
                bit_depth=24
            )
            
            # Generate SFX
            import asyncio
            result = asyncio.run(sfx_client.generate_sfx(generation_request, use_cache=True))
            
            if not result.success:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"SFX generation failed: {result.error_message}"
                )
            
            return SFXGenerationResponse(
                success=True,
                message=f"SFX generated successfully: {result.duration:.2f}s, {result.tiles_generated} tiles",
                result={
                    "duration": result.duration,
                    "tiles_generated": result.tiles_generated,
                    "generation_time": result.generation_time,
                    "sample_rate": result.sample_rate,
                    "bit_depth": result.bit_depth,
                    "file_size": len(result.audio_data),
                    "seed_used": result.seed_used
                }
            )
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"SFX generation failed: {str(e)}"
        )


@router.post("/generate-ambience", response_model=SFXGenerationResponse)
def generate_ambience(
    request: AmbienceGenerationRequestModel,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Generate loopable ambience audio from text prompt
    
    This endpoint generates seamless loopable ambience audio optimized for background
    soundscapes. The generated audio is specifically designed for continuous looping
    without audible seams.
    
    **Ambience Features:**
    - Optimized for seamless looping
    - Longer crossfade durations for smooth transitions
    - Perfect for background ambience and soundscapes
    - High-quality output: 48kHz/24-bit WAV
    - Automatic tiling for longer durations
    
    **Looping Optimization:**
    - Crossfade applied to start/end of audio
    - Seamless loop points created
    - No audible clicks or pops
    - Perfect for continuous playback
    
    Args:
        request: Ambience generation request parameters
        background_tasks: FastAPI background tasks
        db: Database session
        current_user: Current authenticated user
    
    Returns:
        Generation response with task ID or results
    
    Raises:
        HTTPException: 404 if scene not found, 400 if generation fails
    """
    # Verify scene exists if provided
    if request.scene_id:
        scene = db.query(Scene).filter(Scene.id == request.scene_id).first()
        if not scene:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Scene not found"
            )
    
    try:
        if request.async_processing:
            # Process asynchronously
            task = generate_ambience_task.delay(
                prompt=request.prompt,
                duration=request.duration,
                seed=request.seed,
                crossfade_duration=request.crossfade_duration,
                scene_id=request.scene_id,
                asset_name=request.asset_name
            )
            
            message = f"Started ambience generation: {request.prompt[:50]}... (loopable)"
            
            return SFXGenerationResponse(
                success=True,
                message=message,
                task_id=task.id
            )
        
        else:
            # Process synchronously
            sfx_client = ElevenLabsSFXClient()
            
            # Create generation request for loopable ambience
            generation_request = SFXGenerationRequest(
                prompt=request.prompt,
                duration=request.duration,
                seed=request.seed,
                loopable=True,  # Force loopable for ambience
                crossfade_duration=request.crossfade_duration,
                output_format="wav",
                sample_rate=48000,
                bit_depth=24
            )
            
            # Generate ambience
            import asyncio
            result = asyncio.run(sfx_client.generate_sfx(generation_request, use_cache=True))
            
            if not result.success:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Ambience generation failed: {result.error_message}"
                )
            
            return SFXGenerationResponse(
                success=True,
                message=f"Ambience generated successfully: {result.duration:.2f}s, {result.tiles_generated} tiles",
                result={
                    "duration": result.duration,
                    "tiles_generated": result.tiles_generated,
                    "generation_time": result.generation_time,
                    "sample_rate": result.sample_rate,
                    "bit_depth": result.bit_depth,
                    "file_size": len(result.audio_data),
                    "seed_used": result.seed_used,
                    "loopable": True
                }
            )
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Ambience generation failed: {str(e)}"
        )


@router.get("/status/{task_id}", response_model=SFXStatusResponse)
def get_sfx_status(
    task_id: str,
    current_user: User = Depends(get_current_active_user)
):
    """
    Get status of SFX generation task
    
    This endpoint provides real-time status updates for SFX generation tasks,
    including progress information and results when completed.
    
    Args:
        task_id: Celery task ID
        current_user: Current authenticated user
    
    Returns:
        Task status with progress or results
    
    Raises:
        HTTPException: 404 if task not found
    """
    from ....celery_app import celery_app
    
    try:
        task = celery_app.AsyncResult(task_id)
        
        if task.state == 'PENDING':
            return SFXStatusResponse(
                task_id=task_id,
                status='PENDING',
                progress={'current': 0, 'total': 100, 'status': 'Task is waiting to be processed...'}
            )
        
        elif task.state == 'PROGRESS':
            return SFXStatusResponse(
                task_id=task_id,
                status='PROGRESS',
                progress=task.info
            )
        
        elif task.state == 'SUCCESS':
            return SFXStatusResponse(
                task_id=task_id,
                status='SUCCESS',
                result=task.result
            )
        
        elif task.state == 'FAILURE':
            return SFXStatusResponse(
                task_id=task_id,
                status='FAILURE',
                error=str(task.info)
            )
        
        else:
            return SFXStatusResponse(
                task_id=task_id,
                status=task.state,
                progress=task.info
            )
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Task not found: {str(e)}"
        )


@router.get("/cache/info", response_model=SFXCacheInfoResponse)
def get_sfx_cache_info(
    current_user: User = Depends(get_current_active_user)
):
    """
    Get SFX generation cache information
    
    This endpoint provides information about the SFX generation cache,
    including file count and total size.
    
    Args:
        current_user: Current authenticated user
    
    Returns:
        Cache information
    """
    try:
        sfx_client = ElevenLabsSFXClient()
        cache_info = sfx_client.get_cache_info()
        
        return SFXCacheInfoResponse(
            cache_dir=cache_info["cache_dir"],
            total_files=cache_info["total_files"],
            total_size_bytes=cache_info["total_size_bytes"],
            total_size_mb=cache_info["total_size_mb"]
        )
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to get cache info: {str(e)}"
        )


@router.delete("/cache")
def clear_sfx_cache(
    pattern: str = "*",
    background_tasks: BackgroundTasks = None,
    current_user: User = Depends(get_current_active_user)
):
    """
    Clear SFX generation cache
    
    This endpoint clears cached SFX generation results to free up disk space
    or force fresh generation.
    
    Args:
        pattern: Cache file pattern to clear (default: all)
        background_tasks: FastAPI background tasks
        current_user: Current authenticated user
    
    Returns:
        Success message with cleared count
    """
    try:
        if background_tasks:
            # Clear cache asynchronously
            task = clear_sfx_cache_task.delay(pattern)
            message = f"Started clearing SFX cache with pattern: {pattern}"
        else:
            # Clear cache synchronously
            sfx_client = ElevenLabsSFXClient()
            cleared_count = sfx_client.clear_cache(pattern)
            message = f"Cleared {cleared_count} cached SFX results"
        
        return {"success": True, "message": message}
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to clear cache: {str(e)}"
        )


@router.get("/generated-assets/{scene_id}")
def get_generated_assets(
    scene_id: int,
    asset_type: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Get generated SFX/ambience assets for a scene
    
    This endpoint retrieves all generated SFX and ambience assets for a scene,
    including metadata about the generation process.
    
    Args:
        scene_id: Scene ID
        asset_type: Asset type filter (sfx, ambience, or None for all)
        db: Database session
        current_user: Current authenticated user
    
    Returns:
        List of generated assets with metadata
    
    Raises:
        HTTPException: 404 if scene not found
    """
    # Verify scene exists
    scene = db.query(Scene).filter(Scene.id == scene_id).first()
    if not scene:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Scene not found"
        )
    
    # Build query
    query = db.query(Asset).filter(
        Asset.scene_id == scene_id,
        Asset.metadata.has_key("generated")  # Only generated assets
    )
    
    if asset_type:
        query = query.filter(Asset.asset_type == asset_type)
    
    assets = query.all()
    
    # Format response
    generated_assets = []
    for asset in assets:
        metadata = asset.metadata or {}
        generated_assets.append({
            "id": asset.id,
            "name": asset.name,
            "description": asset.description,
            "asset_type": asset.asset_type,
            "duration": asset.duration,
            "file_size": asset.file_size,
            "sample_rate": asset.sample_rate,
            "bit_depth": asset.bit_rate // asset.sample_rate if asset.sample_rate else None,
            "loop": asset.loop,
            "created_at": asset.created_at.isoformat(),
            "generation_metadata": {
                "prompt": metadata.get("prompt"),
                "seed": metadata.get("seed"),
                "loopable": metadata.get("loopable"),
                "tiles_generated": metadata.get("tiles_generated"),
                "generation_time": metadata.get("generation_time"),
                "generated_at": metadata.get("generated_at")
            }
        })
    
    return {
        "scene_id": scene_id,
        "scene_name": scene.name,
        "total_assets": len(generated_assets),
        "assets": generated_assets
    }
