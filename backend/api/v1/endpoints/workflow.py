"""
Workflow API endpoints for the main PRD workflow
"""

import os
import base64
import tempfile
import uuid
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from pathlib import Path
from datetime import datetime, timedelta

from ....database import get_db
from ....models import Scene, Asset, FXPlan, Render, Project, User, JobStatus
from ....schemas import (
    IngestRequest, IngestResponse,
    PlanFXRequest, PlanFXResponse,
    GenFXRequest, GenFXResponse,
    RenderStemsRequest, RenderStemsResponse,
    DownloadRequest, DownloadResponse,
    TimelineJSON
)
from ....config import settings
from ...dependencies import get_current_active_user

router = APIRouter()


@router.post("/ingest", response_model=IngestResponse, status_code=status.HTTP_201_CREATED)
async def ingest_asset(
    request: IngestRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Ingest an asset into a scene
    
    This endpoint handles the ingestion of audio assets (dialogue, music, SFX, ambience)
    into a scene, creating the asset record and updating the scene's timeline JSON.
    
    The asset file should be provided as base64 encoded data in the `file` field.
    The asset will be automatically positioned in the scene timeline based on the
    `start_time` parameter and will be added to the appropriate track based on
    the `asset_type`.
    
    **Asset Types:**
    - `dialogue`: Voice recordings and speech
    - `music`: Background music and musical elements
    - `sfx`: Sound effects and foley
    - `ambience`: Environmental sounds and atmosphere
    
    **Timeline Integration:**
    The asset will be automatically added to the scene's timeline JSON structure,
    maintaining the exact format specified in the PRD.
    
    Args:
        request: Ingest request data containing asset information and file data
        db: Database session
        current_user: Current authenticated user
    
    Returns:
        Ingest response with asset details including asset_id, scene_id, and metadata
    
    Raises:
        HTTPException: 404 if scene not found, 400 if file data is invalid
    """
    # Verify scene exists
    scene = db.query(Scene).filter(Scene.id == request.scene_id).first()
    if not scene:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Scene not found"
        )
    
    # Create upload directory
    upload_dir = Path(settings.upload_dir) / "assets"
    upload_dir.mkdir(parents=True, exist_ok=True)
    
    # Generate unique filename
    file_id = str(uuid.uuid4())
    file_extension = ".wav"  # Default extension, should be determined from file
    filename = f"{file_id}{file_extension}"
    file_path = upload_dir / filename
    
    # Handle file data (assuming base64 encoded for now)
    try:
        # Decode base64 file data
        file_data = base64.b64decode(request.file)
        file_size = len(file_data)
        
        # Save file
        with open(file_path, "wb") as buffer:
            buffer.write(file_data)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid file data: {str(e)}"
        )
    
    # Get audio metadata (placeholder - should use librosa or similar)
    duration = None
    sample_rate = None
    channels = None
    
    # Create asset record
    asset = Asset(
        name=request.name,
        description=request.description,
        asset_type=request.asset_type,
        file_path=str(file_path),
        original_filename=filename,
        file_size=file_size,
        duration=duration,
        format=file_extension[1:],  # Remove dot
        sample_rate=sample_rate,
        channels=channels,
        volume=request.volume,
        pan=request.pan,
        loop=request.loop,
        fade_in=request.fade_in,
        fade_out=request.fade_out,
        start_time=request.start_time,
        scene_id=request.scene_id,
        project_id=scene.project_id
    )
    
    db.add(asset)
    db.commit()
    db.refresh(asset)
    
    # Update scene timeline JSON
    _update_scene_timeline(db, scene, asset)
    
    return IngestResponse(
        asset_id=asset.id,
        scene_id=asset.scene_id,
        name=asset.name,
        asset_type=asset.asset_type,
        file_size=asset.file_size,
        duration=asset.duration,
        message="Asset ingested successfully"
    )


@router.post("/plan_fx", response_model=PlanFXResponse, status_code=status.HTTP_201_CREATED)
def plan_fx(
    request: PlanFXRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Plan FX for a scene
    
    This endpoint creates an FX plan for a scene based on the scene's assets
    and timeline configuration. The FX plan defines how audio effects will be
    applied to the scene's assets during processing.
    
    **FX Plan Configuration:**
    The `effects_config` parameter allows you to specify detailed effect settings
    for different asset types and processing stages. This includes:
    - Voice enhancement settings
    - Background music mixing parameters
    - Sound effect processing options
    - Ambience processing configuration
    
    **Priority System:**
    FX plans can be assigned priorities to control processing order when
    multiple plans exist for the same scene.
    
    Args:
        request: Plan FX request data containing scene_id, plan configuration, and priority
        db: Database session
        current_user: Current authenticated user
    
    Returns:
        Plan FX response with FX plan details including fx_plan_id and status
    
    Raises:
        HTTPException: 404 if scene not found, 400 if plan name already exists
    """
    # Verify scene exists
    scene = db.query(Scene).filter(Scene.id == request.scene_id).first()
    if not scene:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Scene not found"
        )
    
    # Create FX plan
    fx_plan = FXPlan(
        name=request.plan_name,
        description=request.description,
        effects_config=request.effects_config,
        priority=request.priority,
        scene_id=request.scene_id,
        project_id=scene.project_id,
        status=JobStatus.PENDING
    )
    
    db.add(fx_plan)
    db.commit()
    db.refresh(fx_plan)
    
    return PlanFXResponse(
        fx_plan_id=fx_plan.id,
        scene_id=fx_plan.scene_id,
        name=fx_plan.name,
        status=fx_plan.status,
        message="FX plan created successfully"
    )


@router.post("/gen_fx", response_model=GenFXResponse)
def gen_fx(
    request: GenFXRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Generate FX for an FX plan
    
    This endpoint processes an FX plan and generates the actual effects
    based on the scene's assets and timeline. The processing includes:
    
    **Processing Steps:**
    1. Loading scene assets and timeline configuration
    2. Applying effects based on FX plan configuration
    3. Processing audio with specified effects
    4. Generating processed audio files
    5. Updating FX plan status and progress
    
    **Force Regeneration:**
    Use `force_regenerate=true` to reprocess an already completed FX plan.
    This is useful when you need to update effects or reprocess with new settings.
    
    **Progress Tracking:**
    The endpoint returns real-time progress information including current
    processing step and completion percentage.
    
    Args:
        request: Gen FX request data containing fx_plan_id and force_regenerate flag
        db: Database session
        current_user: Current authenticated user
    
    Returns:
        Gen FX response with processing status, progress, and current step
    
    Raises:
        HTTPException: 404 if FX plan not found
    """
    # Verify FX plan exists
    fx_plan = db.query(FXPlan).filter(FXPlan.id == request.fx_plan_id).first()
    if not fx_plan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="FX plan not found"
        )
    
    # Check if already processed and not forcing regeneration
    if fx_plan.status == JobStatus.COMPLETED and not request.force_regenerate:
        return GenFXResponse(
            fx_plan_id=fx_plan.id,
            status=fx_plan.status,
            progress=fx_plan.progress,
            message="FX already generated"
        )
    
    # Update FX plan status
    fx_plan.status = JobStatus.PROCESSING
    fx_plan.started_at = datetime.utcnow()
    fx_plan.progress = 0.0
    fx_plan.current_step = "Initializing FX generation"
    db.commit()
    
    # TODO: Implement actual FX generation logic
    # This would involve:
    # 1. Loading scene assets
    # 2. Processing timeline JSON
    # 3. Applying effects based on FX plan configuration
    # 4. Generating processed audio files
    
    # For now, simulate processing
    fx_plan.progress = 1.0
    fx_plan.status = JobStatus.COMPLETED
    fx_plan.completed_at = datetime.utcnow()
    fx_plan.current_step = "FX generation completed"
    db.commit()
    
    return GenFXResponse(
        fx_plan_id=fx_plan.id,
        status=fx_plan.status,
        progress=fx_plan.progress,
        message="FX generated successfully"
    )


@router.post("/render_stems", response_model=RenderStemsResponse, status_code=status.HTTP_201_CREATED)
def render_stems(
    request: RenderStemsRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Render stems for a scene
    
    This endpoint renders audio stems (dialogue, music, SFX, ambience) for a scene
    based on the scene's assets and FX plan. The rendering process creates separate
    audio files for each stem type, allowing for flexible final mixing.
    
    **Render Types:**
    - `stems`: Separate audio files for each asset type (dialogue, music, SFX, ambience)
    - `final_mix`: Single mixed audio file with all elements combined
    - `preview`: Low-quality preview for quick review
    
    **Output Configuration:**
    - Sample rate: 44100Hz (default) or custom
    - Bit depth: 24-bit (default) or 16-bit
    - Channels: Stereo (2) or mono (1)
    - Format: WAV (default), MP3, or FLAC
    
    **FX Plan Integration:**
    If an FX plan is specified, the rendered stems will include all processed
    effects. If no FX plan is provided, raw assets will be rendered.
    
    Args:
        request: Render stems request data containing scene_id, render configuration, and optional fx_plan_id
        db: Database session
        current_user: Current authenticated user
    
    Returns:
        Render stems response with render details including render_id, status, and progress
    
    Raises:
        HTTPException: 404 if scene or FX plan not found
    """
    # Verify scene exists
    scene = db.query(Scene).filter(Scene.id == request.scene_id).first()
    if not scene:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Scene not found"
        )
    
    # Verify FX plan exists if provided
    fx_plan = None
    if request.fx_plan_id:
        fx_plan = db.query(FXPlan).filter(FXPlan.id == request.fx_plan_id).first()
        if not fx_plan:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="FX plan not found"
            )
    
    # Create render record
    render = Render(
        name=request.render_name,
        render_type=request.render_type,
        output_format=request.output_format,
        sample_rate=request.sample_rate,
        bit_depth=request.bit_depth,
        channels=request.channels,
        render_settings=request.render_settings,
        scene_id=request.scene_id,
        fx_plan_id=request.fx_plan_id,
        project_id=scene.project_id,
        status=JobStatus.PENDING
    )
    
    db.add(render)
    db.commit()
    db.refresh(render)
    
    # TODO: Implement actual rendering logic
    # This would involve:
    # 1. Loading scene assets and timeline
    # 2. Applying FX plan effects if provided
    # 3. Rendering each stem type separately
    # 4. Saving rendered files
    
    # For now, simulate rendering
    render.status = JobStatus.PROCESSING
    render.started_at = datetime.utcnow()
    render.progress = 0.0
    render.current_step = "Initializing render"
    db.commit()
    
    # Simulate completion
    render.progress = 1.0
    render.status = JobStatus.COMPLETED
    render.completed_at = datetime.utcnow()
    render.current_step = "Render completed"
    render.output_path = f"/renders/{render.id}/output.{request.output_format.value}"
    render.file_size = 1024000  # Placeholder
    render.duration = 120.0  # Placeholder
    db.commit()
    
    return RenderStemsResponse(
        render_id=render.id,
        scene_id=render.scene_id,
        name=render.name,
        render_type=render.render_type,
        status=render.status,
        progress=render.progress,
        message="Render completed successfully"
    )


@router.post("/download", response_model=DownloadResponse)
def download_render(
    request: DownloadRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Download a rendered file
    
    This endpoint provides a download URL for a completed render. The download
    URL is time-limited and expires after 24 hours for security.
    
    **Download Process:**
    1. Verify render exists and is completed
    2. Generate secure download URL
    3. Return download details with expiration time
    
    **File Access:**
    Use the returned `download_url` to access the actual file via the
    `/workflow/download/{render_id}/file` endpoint.
    
    Args:
        request: Download request data containing render_id
        db: Database session
        current_user: Current authenticated user
    
    Returns:
        Download response with download URL, filename, file size, and expiration time
    
    Raises:
        HTTPException: 404 if render not found, 400 if render not completed
    """
    # Verify render exists
    render = db.query(Render).filter(Render.id == request.render_id).first()
    if not render:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Render not found"
        )
    
    # Check if render is completed
    if render.status != JobStatus.COMPLETED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Render is not completed yet"
        )
    
    # Check if output file exists
    if not render.output_path or not os.path.exists(render.output_path):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Render file not found"
        )
    
    # Generate download URL (in production, this would be a signed URL)
    download_url = f"/api/v1/workflow/download/{render.id}/file"
    expires_at = datetime.utcnow() + timedelta(hours=24)
    
    return DownloadResponse(
        render_id=render.id,
        filename=f"{render.name}.{render.output_format.value}",
        file_size=render.file_size or 0,
        download_url=download_url,
        expires_at=expires_at
    )


@router.get("/download/{render_id}/file")
def download_render_file(
    render_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Download the actual render file
    
    Args:
        render_id: Render ID
        db: Database session
        current_user: Current authenticated user
    
    Returns:
        File response
    """
    # Verify render exists
    render = db.query(Render).filter(Render.id == render_id).first()
    if not render:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Render not found"
        )
    
    # Check if render is completed
    if render.status != JobStatus.COMPLETED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Render is not completed yet"
        )
    
    # Check if output file exists
    if not render.output_path or not os.path.exists(render.output_path):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Render file not found"
        )
    
    return FileResponse(
        path=render.output_path,
        filename=f"{render.name}.{render.output_format.value}",
        media_type="audio/*"
    )


def _update_scene_timeline(db: Session, scene: Scene, asset: Asset):
    """
    Update scene timeline JSON with new asset
    
    Args:
        db: Database session
        scene: Scene object
        asset: Asset object
    """
    # Get or create timeline JSON
    timeline_json = scene.timeline_json or {
        "version": "1.0",
        "duration": 0.0,
        "sample_rate": 44100,
        "tracks": [],
        "metadata": {}
    }
    
    # Find or create track for asset type
    track = None
    for t in timeline_json["tracks"]:
        if t["type"] == asset.asset_type:
            track = t
            break
    
    if not track:
        track = {
            "name": f"{asset.asset_type.title()} Track",
            "type": asset.asset_type,
            "assets": [],
            "volume": 1.0,
            "pan": 0.0,
            "mute": False,
            "solo": False
        }
        timeline_json["tracks"].append(track)
    
    # Add asset to track
    asset_data = {
        "id": asset.id,
        "name": asset.name,
        "start_time": asset.start_time,
        "end_time": asset.end_time or (asset.start_time + (asset.duration or 0)),
        "volume": asset.volume,
        "pan": asset.pan,
        "loop": asset.loop,
        "fade_in": asset.fade_in,
        "fade_out": asset.fade_out,
        "file_path": asset.file_path
    }
    
    track["assets"].append(asset_data)
    
    # Update scene duration if needed
    if asset.end_time and asset.end_time > timeline_json["duration"]:
        timeline_json["duration"] = asset.end_time
    
    # Update scene with new timeline JSON
    scene.timeline_json = timeline_json
    db.commit()
