"""
Celery tasks for SFX generation
"""

import logging
from typing import Dict, Any, Optional
from celery import current_task
from sqlalchemy.orm import Session

from ..celery_app import celery_app
from ..database import get_db
from ..models import Asset, Scene, Project
from ..services.elevenlabs_sfx import ElevenLabsSFXClient, SFXGenerationRequest, SFXGenerationResult

logger = logging.getLogger(__name__)


@celery_app.task(bind=True, name="generate_sfx")
def generate_sfx_task(self, prompt: str, duration: float, seed: Optional[int] = None,
                     loopable: bool = False, crossfade_duration: float = 0.5,
                     scene_id: Optional[int] = None, asset_name: Optional[str] = None) -> Dict[str, Any]:
    """
    Celery task to generate SFX audio using ElevenLabs
    
    Args:
        prompt: Text prompt for SFX generation
        duration: Duration in seconds
        seed: Fixed seed for deterministic generation
        loopable: Whether to generate loopable ambience
        crossfade_duration: Crossfade duration for tiling
        scene_id: Scene ID to associate with generated asset
        asset_name: Name for the generated asset
        
    Returns:
        Dictionary with generation results
    """
    try:
        # Update task status
        current_task.update_state(
            state='PROGRESS',
            meta={'current': 0, 'total': 100, 'status': 'Starting SFX generation...'}
        )
        
        # Initialize SFX client
        sfx_client = ElevenLabsSFXClient()
        
        # Update progress
        current_task.update_state(
            state='PROGRESS',
            meta={'current': 10, 'total': 100, 'status': 'Preparing generation request...'}
        )
        
        # Create generation request
        request = SFXGenerationRequest(
            prompt=prompt,
            duration=duration,
            seed=seed,
            loopable=loopable,
            crossfade_duration=crossfade_duration,
            output_format="wav",
            sample_rate=48000,
            bit_depth=24
        )
        
        # Update progress
        current_task.update_state(
            state='PROGRESS',
            meta={'current': 20, 'total': 100, 'status': 'Generating SFX audio...'}
        )
        
        # Generate SFX (run async function in sync context)
        import asyncio
        result = asyncio.run(sfx_client.generate_sfx(request, use_cache=True))
        
        if not result.success:
            raise Exception(f"SFX generation failed: {result.error_message}")
        
        # Update progress
        current_task.update_state(
            state='PROGRESS',
            meta={'current': 80, 'total': 100, 'status': 'Saving generated audio...'}
        )
        
        # Save to database if scene_id provided
        asset_id = None
        if scene_id:
            db = next(get_db())
            try:
                # Get scene
                scene = db.query(Scene).filter(Scene.id == scene_id).first()
                if not scene:
                    raise ValueError(f"Scene {scene_id} not found")
                
                # Generate asset name if not provided
                if not asset_name:
                    asset_name = f"Generated SFX: {prompt[:50]}..."
                
                # Save audio file
                import tempfile
                import os
                from pathlib import Path
                
                # Create upload directory
                upload_dir = Path(settings.upload_dir) / "sfx"
                upload_dir.mkdir(parents=True, exist_ok=True)
                
                # Generate filename
                import uuid
                file_id = str(uuid.uuid4())
                filename = f"{file_id}.wav"
                file_path = upload_dir / filename
                
                # Write audio data
                with open(file_path, 'wb') as f:
                    f.write(result.audio_data)
                
                # Create asset record
                asset = Asset(
                    name=asset_name,
                    description=f"Generated SFX: {prompt}",
                    asset_type="sfx",
                    file_path=str(file_path),
                    original_filename=filename,
                    file_size=len(result.audio_data),
                    duration=result.duration,
                    format="wav",
                    sample_rate=result.sample_rate,
                    channels=1,  # Mono
                    bit_rate=result.sample_rate * result.bit_depth,
                    scene_id=scene_id,
                    project_id=scene.project_id,
                    metadata={
                        "generated": True,
                        "prompt": prompt,
                        "seed": seed,
                        "loopable": loopable,
                        "tiles_generated": result.tiles_generated,
                        "generation_time": result.generation_time,
                        "generated_at": datetime.now().isoformat()
                    }
                )
                
                db.add(asset)
                db.commit()
                db.refresh(asset)
                asset_id = asset.id
                
                logger.info(f"Created asset {asset_id} for generated SFX")
                
            except Exception as e:
                logger.error(f"Failed to save generated SFX to database: {e}")
                db.rollback()
            finally:
                db.close()
        
        # Update progress
        current_task.update_state(
            state='PROGRESS',
            meta={'current': 100, 'total': 100, 'status': 'SFX generation completed!'}
        )
        
        return {
            "success": True,
            "prompt": prompt,
            "duration": result.duration,
            "seed": result.seed_used,
            "loopable": loopable,
            "tiles_generated": result.tiles_generated,
            "generation_time": result.generation_time,
            "sample_rate": result.sample_rate,
            "bit_depth": result.bit_depth,
            "file_size": len(result.audio_data),
            "scene_id": scene_id,
            "asset_id": asset_id,
            "asset_name": asset_name
        }
        
    except Exception as e:
        logger.error(f"SFX generation task failed: {e}")
        current_task.update_state(
            state='FAILURE',
            meta={'error': str(e), 'status': 'SFX generation failed'}
        )
        raise


@celery_app.task(bind=True, name="generate_ambience")
def generate_ambience_task(self, prompt: str, duration: float, seed: Optional[int] = None,
                          crossfade_duration: float = 1.0, scene_id: Optional[int] = None,
                          asset_name: Optional[str] = None) -> Dict[str, Any]:
    """
    Celery task to generate loopable ambience using ElevenLabs
    
    Args:
        prompt: Text prompt for ambience generation
        duration: Duration in seconds
        seed: Fixed seed for deterministic generation
        crossfade_duration: Crossfade duration for seamless looping
        scene_id: Scene ID to associate with generated asset
        asset_name: Name for the generated asset
        
    Returns:
        Dictionary with generation results
    """
    try:
        # Update task status
        current_task.update_state(
            state='PROGRESS',
            meta={'current': 0, 'total': 100, 'status': 'Starting ambience generation...'}
        )
        
        # Initialize SFX client
        sfx_client = ElevenLabsSFXClient()
        
        # Update progress
        current_task.update_state(
            state='PROGRESS',
            meta={'current': 10, 'total': 100, 'status': 'Preparing ambience request...'}
        )
        
        # Create generation request for loopable ambience
        request = SFXGenerationRequest(
            prompt=prompt,
            duration=duration,
            seed=seed,
            loopable=True,  # Force loopable for ambience
            crossfade_duration=crossfade_duration,
            output_format="wav",
            sample_rate=48000,
            bit_depth=24
        )
        
        # Update progress
        current_task.update_state(
            state='PROGRESS',
            meta={'current': 20, 'total': 100, 'status': 'Generating loopable ambience...'}
        )
        
        # Generate ambience (run async function in sync context)
        import asyncio
        result = asyncio.run(sfx_client.generate_sfx(request, use_cache=True))
        
        if not result.success:
            raise Exception(f"Ambience generation failed: {result.error_message}")
        
        # Update progress
        current_task.update_state(
            state='PROGRESS',
            meta={'current': 80, 'total': 100, 'status': 'Saving generated ambience...'}
        )
        
        # Save to database if scene_id provided
        asset_id = None
        if scene_id:
            db = next(get_db())
            try:
                # Get scene
                scene = db.query(Scene).filter(Scene.id == scene_id).first()
                if not scene:
                    raise ValueError(f"Scene {scene_id} not found")
                
                # Generate asset name if not provided
                if not asset_name:
                    asset_name = f"Generated Ambience: {prompt[:50]}..."
                
                # Save audio file
                import tempfile
                import os
                from pathlib import Path
                
                # Create upload directory
                upload_dir = Path(settings.upload_dir) / "ambience"
                upload_dir.mkdir(parents=True, exist_ok=True)
                
                # Generate filename
                import uuid
                file_id = str(uuid.uuid4())
                filename = f"{file_id}.wav"
                file_path = upload_dir / filename
                
                # Write audio data
                with open(file_path, 'wb') as f:
                    f.write(result.audio_data)
                
                # Create asset record
                asset = Asset(
                    name=asset_name,
                    description=f"Generated Ambience: {prompt}",
                    asset_type="ambience",
                    file_path=str(file_path),
                    original_filename=filename,
                    file_size=len(result.audio_data),
                    duration=result.duration,
                    format="wav",
                    sample_rate=result.sample_rate,
                    channels=1,  # Mono
                    bit_rate=result.sample_rate * result.bit_depth,
                    loop=True,  # Mark as loopable
                    scene_id=scene_id,
                    project_id=scene.project_id,
                    metadata={
                        "generated": True,
                        "prompt": prompt,
                        "seed": seed,
                        "loopable": True,
                        "tiles_generated": result.tiles_generated,
                        "generation_time": result.generation_time,
                        "generated_at": datetime.now().isoformat()
                    }
                )
                
                db.add(asset)
                db.commit()
                db.refresh(asset)
                asset_id = asset.id
                
                logger.info(f"Created asset {asset_id} for generated ambience")
                
            except Exception as e:
                logger.error(f"Failed to save generated ambience to database: {e}")
                db.rollback()
            finally:
                db.close()
        
        # Update progress
        current_task.update_state(
            state='PROGRESS',
            meta={'current': 100, 'total': 100, 'status': 'Ambience generation completed!'}
        )
        
        return {
            "success": True,
            "prompt": prompt,
            "duration": result.duration,
            "seed": result.seed_used,
            "loopable": True,
            "tiles_generated": result.tiles_generated,
            "generation_time": result.generation_time,
            "sample_rate": result.sample_rate,
            "bit_depth": result.bit_depth,
            "file_size": len(result.audio_data),
            "scene_id": scene_id,
            "asset_id": asset_id,
            "asset_name": asset_name
        }
        
    except Exception as e:
        logger.error(f"Ambience generation task failed: {e}")
        current_task.update_state(
            state='FAILURE',
            meta={'error': str(e), 'status': 'Ambience generation failed'}
        )
        raise


@celery_app.task(bind=True, name="clear_sfx_cache")
def clear_sfx_cache_task(self, pattern: str = "*") -> Dict[str, Any]:
    """
    Celery task to clear SFX generation cache
    
    Args:
        pattern: Cache file pattern to clear
        
    Returns:
        Dictionary with cache clearing results
    """
    try:
        # Update task status
        current_task.update_state(
            state='PROGRESS',
            meta={'current': 0, 'total': 100, 'status': 'Clearing SFX cache...'}
        )
        
        # Initialize SFX client
        sfx_client = ElevenLabsSFXClient()
        
        # Clear cache
        cleared_count = sfx_client.clear_cache(pattern)
        
        # Update progress
        current_task.update_state(
            state='PROGRESS',
            meta={'current': 100, 'total': 100, 'status': 'Cache cleared!'}
        )
        
        return {
            "success": True,
            "pattern": pattern,
            "cleared_count": cleared_count,
            "message": f"Cleared {cleared_count} cached SFX results"
        }
        
    except Exception as e:
        logger.error(f"SFX cache clearing task failed: {e}")
        current_task.update_state(
            state='FAILURE',
            meta={'error': str(e), 'status': 'Cache clearing failed'}
        )
        raise
