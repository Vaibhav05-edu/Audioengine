"""
Audio alignment API endpoints
"""

from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field

from ....database import get_db
from ....models import Scene, Asset, User
from ....services.alignment import WhisperXAlignmentService, AlignmentResult
from ....tasks.alignment_tasks import align_vo_asset_task, align_scene_vo_task, clear_alignment_cache_task
from ...dependencies import get_current_active_user

router = APIRouter()


class AlignVORequest(BaseModel):
    """Request model for VO alignment"""
    scene_id: int = Field(..., description="Scene ID to align")
    asset_id: Optional[int] = Field(None, description="Specific asset ID to align (optional)")
    language: Optional[str] = Field(None, description="Language code (auto-detect if None)")
    force_reprocess: bool = Field(default=False, description="Force reprocessing even if cached")
    async_processing: bool = Field(default=True, description="Process asynchronously")


class AlignVOResponse(BaseModel):
    """Response model for VO alignment"""
    success: bool
    message: str
    scene_id: int
    asset_id: Optional[int]
    task_id: Optional[str] = None
    results: Optional[Dict[str, Any]] = None


class AlignmentStatusResponse(BaseModel):
    """Response model for alignment status"""
    task_id: str
    status: str
    progress: Optional[Dict[str, Any]] = None
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


class AlignmentResultResponse(BaseModel):
    """Response model for alignment results"""
    scene_id: int
    asset_id: int
    language: str
    total_segments: int
    total_words: int
    total_duration: float
    average_confidence: float
    processing_time: float
    model_used: str
    created_at: str
    segments: List[Dict[str, Any]]


@router.post("/align_vo", response_model=AlignVOResponse)
def align_vo(
    request: AlignVORequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Align voice-over audio files to produce word-level timestamps
    
    This endpoint uses WhisperX to align voice-over audio files and produce
    word-level timestamps. It can process individual assets or all VO assets
    in a scene.
    
    **Alignment Features:**
    - Word-level timestamp extraction
    - Automatic language detection
    - Confidence scoring for each word
    - Caching of results for performance
    - Async processing support
    
    **Processing Options:**
    - `asset_id`: Align specific asset (if None, aligns all VO assets in scene)
    - `language`: Force specific language (auto-detect if None)
    - `force_reprocess`: Bypass cache and reprocess
    - `async_processing`: Process in background (recommended)
    
    **Caching:**
    Results are automatically cached based on file content and metadata.
    Cache keys are generated using file modification time and size.
    
    Args:
        request: Alignment request parameters
        background_tasks: FastAPI background tasks
        db: Database session
        current_user: Current authenticated user
    
    Returns:
        Alignment response with task ID or results
    
    Raises:
        HTTPException: 404 if scene/asset not found, 400 if processing fails
    """
    # Verify scene exists
    scene = db.query(Scene).filter(Scene.id == request.scene_id).first()
    if not scene:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Scene not found"
        )
    
    # Verify asset exists if specified
    if request.asset_id:
        asset = db.query(Asset).filter(Asset.id == request.asset_id).first()
        if not asset:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Asset not found"
            )
        
        if asset.scene_id != request.scene_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Asset does not belong to the specified scene"
            )
    
    try:
        if request.async_processing:
            # Process asynchronously
            if request.asset_id:
                task = align_vo_asset_task.delay(
                    request.scene_id,
                    request.asset_id,
                    request.language,
                    request.force_reprocess
                )
                message = f"Started alignment for asset {request.asset_id} in scene {request.scene_id}"
            else:
                task = align_scene_vo_task.delay(
                    request.scene_id,
                    request.language,
                    request.force_reprocess
                )
                message = f"Started alignment for all VO assets in scene {request.scene_id}"
            
            return AlignVOResponse(
                success=True,
                message=message,
                scene_id=request.scene_id,
                asset_id=request.asset_id,
                task_id=task.id
            )
        
        else:
            # Process synchronously
            alignment_service = WhisperXAlignmentService()
            
            if request.asset_id:
                # Align specific asset
                asset = db.query(Asset).filter(Asset.id == request.asset_id).first()
                alignment_result = alignment_service.align_audio(
                    asset.file_path,
                    request.scene_id,
                    request.asset_id,
                    request.language,
                    request.force_reprocess
                )
                
                summary = alignment_service.get_alignment_summary(alignment_result)
                results = {
                    "asset_id": request.asset_id,
                    "asset_name": asset.name,
                    "summary": summary,
                    "alignment_result": alignment_result
                }
                
                message = f"Alignment completed for asset {request.asset_id}"
            else:
                # Align all VO assets in scene
                results = alignment_service.align_scene_vo(
                    request.scene_id,
                    db,
                    request.language,
                    request.force_reprocess
                )
                
                message = f"Alignment completed for scene {request.scene_id}"
            
            return AlignVOResponse(
                success=True,
                message=message,
                scene_id=request.scene_id,
                asset_id=request.asset_id,
                results=results
            )
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Alignment failed: {str(e)}"
        )


@router.get("/status/{task_id}", response_model=AlignmentStatusResponse)
def get_alignment_status(
    task_id: str,
    current_user: User = Depends(get_current_active_user)
):
    """
    Get status of alignment task
    
    This endpoint provides real-time status updates for alignment tasks,
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
            return AlignmentStatusResponse(
                task_id=task_id,
                status='PENDING',
                progress={'current': 0, 'total': 100, 'status': 'Task is waiting to be processed...'}
            )
        
        elif task.state == 'PROGRESS':
            return AlignmentStatusResponse(
                task_id=task_id,
                status='PROGRESS',
                progress=task.info
            )
        
        elif task.state == 'SUCCESS':
            return AlignmentStatusResponse(
                task_id=task_id,
                status='SUCCESS',
                result=task.result
            )
        
        elif task.state == 'FAILURE':
            return AlignmentStatusResponse(
                task_id=task_id,
                status='FAILURE',
                error=str(task.info)
            )
        
        else:
            return AlignmentStatusResponse(
                task_id=task_id,
                status=task.state,
                progress=task.info
            )
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Task not found: {str(e)}"
        )


@router.get("/results/{scene_id}", response_model=List[AlignmentResultResponse])
def get_alignment_results(
    scene_id: int,
    asset_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Get cached alignment results for a scene or asset
    
    This endpoint retrieves previously computed alignment results from cache.
    Results include word-level timestamps, confidence scores, and metadata.
    
    Args:
        scene_id: Scene ID
        asset_id: Asset ID (optional, returns all assets if None)
        db: Database session
        current_user: Current authenticated user
    
    Returns:
        List of alignment results
    
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
    
    alignment_service = WhisperXAlignmentService()
    results = []
    
    if asset_id:
        # Get specific asset
        asset = db.query(Asset).filter(Asset.id == asset_id).first()
        if not asset:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Asset not found"
            )
        
        # Try to get cached result
        cached_result = alignment_service.cache.get(scene_id, asset_id, asset.file_path)
        if cached_result:
            results.append(_format_alignment_result(cached_result))
    else:
        # Get all VO assets in scene
        vo_assets = db.query(Asset).filter(
            Asset.scene_id == scene_id,
            Asset.asset_type == "dialogue"
        ).all()
        
        for asset in vo_assets:
            # Check if this is a VO asset
            is_vo = (
                "V.O." in asset.name.upper() or 
                "VOICE OVER" in asset.name.upper() or
                "VOICE-OVER" in asset.name.upper() or
                (asset.metadata and asset.metadata.get("is_voice_over", False))
            )
            
            if not is_vo:
                continue
            
            # Try to get cached result
            cached_result = alignment_service.cache.get(scene_id, asset.id, asset.file_path)
            if cached_result:
                results.append(_format_alignment_result(cached_result))
    
    return results


@router.delete("/cache/{scene_id}")
def clear_alignment_cache(
    scene_id: int,
    asset_id: Optional[int] = None,
    background_tasks: BackgroundTasks = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Clear alignment cache for a scene or asset
    
    This endpoint clears cached alignment results to force reprocessing.
    Useful when audio files have been updated or when you want fresh results.
    
    Args:
        scene_id: Scene ID
        asset_id: Asset ID (optional, clears all assets if None)
        background_tasks: FastAPI background tasks
        db: Database session
        current_user: Current authenticated user
    
    Returns:
        Success message
    
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
    
    if asset_id:
        # Verify asset exists
        asset = db.query(Asset).filter(Asset.id == asset_id).first()
        if not asset:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Asset not found"
            )
    
    try:
        if background_tasks:
            # Clear cache asynchronously
            task = clear_alignment_cache_task.delay(scene_id, asset_id)
            message = f"Started clearing cache for scene {scene_id}"
            if asset_id:
                message += f", asset {asset_id}"
        else:
            # Clear cache synchronously
            alignment_service = WhisperXAlignmentService()
            alignment_service.cache.clear(scene_id, asset_id)
            message = f"Cleared cache for scene {scene_id}"
            if asset_id:
                message += f", asset {asset_id}"
        
        return {"success": True, "message": message}
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to clear cache: {str(e)}"
        )


def _format_alignment_result(alignment_result: AlignmentResult) -> AlignmentResultResponse:
    """Format alignment result for API response"""
    total_words = sum(len(seg.words) for seg in alignment_result.segments)
    avg_confidence = sum(word.confidence for seg in alignment_result.segments for word in seg.words) / total_words if total_words > 0 else 0.0
    
    segments_data = []
    for seg in alignment_result.segments:
        segments_data.append({
            "text": seg.text,
            "start": seg.start,
            "end": seg.end,
            "confidence": seg.confidence,
            "speaker": seg.speaker,
            "words": [
                {
                    "word": word.word,
                    "start": word.start,
                    "end": word.end,
                    "confidence": word.confidence,
                    "speaker": word.speaker
                }
                for word in seg.words
            ]
        })
    
    return AlignmentResultResponse(
        scene_id=alignment_result.scene_id,
        asset_id=alignment_result.asset_id,
        language=alignment_result.language,
        total_segments=len(alignment_result.segments),
        total_words=total_words,
        total_duration=alignment_result.total_duration,
        average_confidence=float(avg_confidence),
        processing_time=alignment_result.processing_time,
        model_used=alignment_result.model_used,
        created_at=alignment_result.created_at.isoformat(),
        segments=segments_data
    )
