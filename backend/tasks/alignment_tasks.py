"""
Celery tasks for audio alignment processing
"""

import logging
from typing import Dict, Any, Optional
from celery import current_task
from sqlalchemy.orm import Session

from ..celery_app import celery_app
from ..database import get_db
from ..models import Scene, Asset
from ..services.alignment import WhisperXAlignmentService

logger = logging.getLogger(__name__)


@celery_app.task(bind=True, name="align_vo_asset")
def align_vo_asset_task(self, scene_id: int, asset_id: int, 
                       language: str = None, force_reprocess: bool = False) -> Dict[str, Any]:
    """
    Celery task to align a single voice-over asset
    
    Args:
        scene_id: Scene ID
        asset_id: Asset ID
        language: Language code (auto-detect if None)
        force_reprocess: Force reprocessing even if cached
        
    Returns:
        Dictionary with alignment results
    """
    try:
        # Update task status
        current_task.update_state(
            state='PROGRESS',
            meta={'current': 0, 'total': 100, 'status': 'Starting alignment...'}
        )
        
        # Get database session
        db = next(get_db())
        
        # Get asset
        asset = db.query(Asset).filter(Asset.id == asset_id).first()
        if not asset:
            raise ValueError(f"Asset {asset_id} not found")
        
        # Get scene
        scene = db.query(Scene).filter(Scene.id == scene_id).first()
        if not scene:
            raise ValueError(f"Scene {scene_id} not found")
        
        # Update progress
        current_task.update_state(
            state='PROGRESS',
            meta={'current': 10, 'total': 100, 'status': 'Loading alignment service...'}
        )
        
        # Initialize alignment service
        alignment_service = WhisperXAlignmentService()
        
        # Update progress
        current_task.update_state(
            state='PROGRESS',
            meta={'current': 20, 'total': 100, 'status': 'Processing audio file...'}
        )
        
        # Align audio
        alignment_result = alignment_service.align_audio(
            asset.file_path,
            scene_id,
            asset_id,
            language,
            force_reprocess
        )
        
        # Update progress
        current_task.update_state(
            state='PROGRESS',
            meta={'current': 90, 'total': 100, 'status': 'Finalizing results...'}
        )
        
        # Get summary
        summary = alignment_service.get_alignment_summary(alignment_result)
        
        # Update progress
        current_task.update_state(
            state='PROGRESS',
            meta={'current': 100, 'total': 100, 'status': 'Alignment completed!'}
        )
        
        return {
            "success": True,
            "scene_id": scene_id,
            "asset_id": asset_id,
            "asset_name": asset.name,
            "summary": summary,
            "alignment_result": {
                "language": alignment_result.language,
                "total_segments": len(alignment_result.segments),
                "total_duration": alignment_result.total_duration,
                "processing_time": alignment_result.processing_time,
                "model_used": alignment_result.model_used,
                "created_at": alignment_result.created_at.isoformat()
            }
        }
        
    except Exception as e:
        logger.error(f"Alignment task failed for scene {scene_id}, asset {asset_id}: {e}")
        current_task.update_state(
            state='FAILURE',
            meta={'error': str(e), 'status': 'Alignment failed'}
        )
        raise
    
    finally:
        if 'db' in locals():
            db.close()


@celery_app.task(bind=True, name="align_scene_vo")
def align_scene_vo_task(self, scene_id: int, language: str = None, 
                       force_reprocess: bool = False) -> Dict[str, Any]:
    """
    Celery task to align all voice-over assets in a scene
    
    Args:
        scene_id: Scene ID
        language: Language code (auto-detect if None)
        force_reprocess: Force reprocessing even if cached
        
    Returns:
        Dictionary with alignment results for all VO assets
    """
    try:
        # Update task status
        current_task.update_state(
            state='PROGRESS',
            meta={'current': 0, 'total': 100, 'status': 'Starting scene alignment...'}
        )
        
        # Get database session
        db = next(get_db())
        
        # Get scene
        scene = db.query(Scene).filter(Scene.id == scene_id).first()
        if not scene:
            raise ValueError(f"Scene {scene_id} not found")
        
        # Get VO assets
        vo_assets = db.query(Asset).filter(
            Asset.scene_id == scene_id,
            Asset.asset_type == "dialogue"
        ).all()
        
        if not vo_assets:
            return {
                "success": True,
                "scene_id": scene_id,
                "scene_name": scene.name,
                "message": "No voice-over assets found",
                "alignments": [],
                "total_assets": 0,
                "successful_alignments": 0,
                "failed_alignments": 0
            }
        
        # Update progress
        current_task.update_state(
            state='PROGRESS',
            meta={'current': 10, 'total': 100, 'status': f'Found {len(vo_assets)} VO assets...'}
        )
        
        # Initialize alignment service
        alignment_service = WhisperXAlignmentService()
        
        # Process each asset
        results = []
        total_assets = len(vo_assets)
        
        for i, asset in enumerate(vo_assets):
            try:
                # Check if this is actually a VO asset
                is_vo = (
                    "V.O." in asset.name.upper() or 
                    "VOICE OVER" in asset.name.upper() or
                    "VOICE-OVER" in asset.name.upper() or
                    (asset.metadata and asset.metadata.get("is_voice_over", False))
                )
                
                if not is_vo:
                    continue
                
                # Update progress
                progress = 10 + (i / total_assets) * 80
                current_task.update_state(
                    state='PROGRESS',
                    meta={
                        'current': int(progress),
                        'total': 100,
                        'status': f'Aligning asset {i+1}/{total_assets}: {asset.name}...'
                    }
                )
                
                # Align audio
                alignment_result = alignment_service.align_audio(
                    asset.file_path,
                    scene_id,
                    asset.id,
                    language,
                    force_reprocess
                )
                
                # Get summary
                summary = alignment_service.get_alignment_summary(alignment_result)
                
                results.append({
                    "asset_id": asset.id,
                    "asset_name": asset.name,
                    "file_path": asset.file_path,
                    "summary": summary,
                    "success": True
                })
                
            except Exception as e:
                logger.error(f"Failed to align asset {asset.id}: {e}")
                results.append({
                    "asset_id": asset.id,
                    "asset_name": asset.name,
                    "file_path": asset.file_path,
                    "error": str(e),
                    "success": False
                })
        
        # Update progress
        current_task.update_state(
            state='PROGRESS',
            meta={'current': 95, 'total': 100, 'status': 'Finalizing results...'}
        )
        
        successful_alignments = len([r for r in results if r["success"]])
        failed_alignments = len([r for r in results if not r["success"]])
        
        # Update progress
        current_task.update_state(
            state='PROGRESS',
            meta={'current': 100, 'total': 100, 'status': 'Scene alignment completed!'}
        )
        
        return {
            "success": True,
            "scene_id": scene_id,
            "scene_name": scene.name,
            "alignments": results,
            "total_assets": total_assets,
            "successful_alignments": successful_alignments,
            "failed_alignments": failed_alignments
        }
        
    except Exception as e:
        logger.error(f"Scene alignment task failed for scene {scene_id}: {e}")
        current_task.update_state(
            state='FAILURE',
            meta={'error': str(e), 'status': 'Scene alignment failed'}
        )
        raise
    
    finally:
        if 'db' in locals():
            db.close()


@celery_app.task(bind=True, name="clear_alignment_cache")
def clear_alignment_cache_task(self, scene_id: int, asset_id: int = None) -> Dict[str, Any]:
    """
    Celery task to clear alignment cache
    
    Args:
        scene_id: Scene ID
        asset_id: Asset ID (optional, clears all assets if None)
        
    Returns:
        Dictionary with cache clearing results
    """
    try:
        # Update task status
        current_task.update_state(
            state='PROGRESS',
            meta={'current': 0, 'total': 100, 'status': 'Clearing alignment cache...'}
        )
        
        # Initialize alignment service
        alignment_service = WhisperXAlignmentService()
        
        if asset_id:
            # Clear specific asset cache
            alignment_service.cache.clear(scene_id, asset_id)
            message = f"Cleared cache for scene {scene_id}, asset {asset_id}"
        else:
            # Clear all assets for scene
            # This would require iterating through all assets in the scene
            # For now, we'll clear the cache directory for the scene
            from pathlib import Path
            cache_dir = Path(alignment_service.cache.cache_dir)
            pattern = f"alignment_{scene_id}_*.json"
            cleared_files = 0
            for cache_file in cache_dir.glob(pattern):
                cache_file.unlink()
                cleared_files += 1
            message = f"Cleared {cleared_files} cache files for scene {scene_id}"
        
        # Update progress
        current_task.update_state(
            state='PROGRESS',
            meta={'current': 100, 'total': 100, 'status': 'Cache cleared!'}
        )
        
        return {
            "success": True,
            "scene_id": scene_id,
            "asset_id": asset_id,
            "message": message
        }
        
    except Exception as e:
        logger.error(f"Cache clearing task failed for scene {scene_id}: {e}")
        current_task.update_state(
            state='FAILURE',
            meta={'error': str(e), 'status': 'Cache clearing failed'}
        )
        raise
