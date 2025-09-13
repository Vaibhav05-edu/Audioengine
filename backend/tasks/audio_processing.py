"""
Audio processing tasks
"""

import os
import tempfile
from pathlib import Path
from typing import Dict, Any, Optional
from celery import current_task
from sqlalchemy.orm import Session

from ..celery_app import celery_app
from ..database import SessionLocal
from ..models import ProcessingJob, JobStatus, AudioFile
from ..config import settings


@celery_app.task(bind=True, name="process_audio_file")
def process_audio_file(
    self,
    job_id: int,
    audio_file_id: int,
    effects_config: Dict[str, Any],
    output_format: str = "wav"
) -> Dict[str, Any]:
    """
    Process an audio file with specified effects
    
    Args:
        job_id: Processing job ID
        audio_file_id: Audio file ID
        effects_config: Effects configuration
        output_format: Output audio format
    
    Returns:
        Dict with processing results
    """
    db = SessionLocal()
    try:
        # Get the processing job
        job = db.query(ProcessingJob).filter(ProcessingJob.id == job_id).first()
        if not job:
            raise ValueError(f"Processing job {job_id} not found")
        
        # Get the audio file
        audio_file = db.query(AudioFile).filter(AudioFile.id == audio_file_id).first()
        if not audio_file:
            raise ValueError(f"Audio file {audio_file_id} not found")
        
        # Update job status
        job.status = JobStatus.PROCESSING
        job.started_at = func.now()
        db.commit()
        
        # Update progress
        self.update_state(
            state="PROGRESS",
            meta={"current": 0, "total": 100, "status": "Starting processing..."}
        )
        
        # Process the audio file
        result = _process_audio_with_effects(
            audio_file.file_path,
            effects_config,
            output_format,
            self
        )
        
        # Update job with results
        job.status = JobStatus.COMPLETED
        job.progress = 1.0
        job.output_path = result["output_path"]
        job.completed_at = func.now()
        db.commit()
        
        return {
            "job_id": job_id,
            "status": "completed",
            "output_path": result["output_path"],
            "processing_time": result["processing_time"],
            "effects_applied": result["effects_applied"]
        }
        
    except Exception as e:
        # Update job with error
        if 'job' in locals():
            job.status = JobStatus.FAILED
            job.error_message = str(e)
            db.commit()
        
        # Re-raise the exception
        raise
    finally:
        db.close()


def _process_audio_with_effects(
    input_path: str,
    effects_config: Dict[str, Any],
    output_format: str,
    task_instance
) -> Dict[str, Any]:
    """
    Internal function to process audio with effects
    
    Args:
        input_path: Path to input audio file
        effects_config: Effects configuration
        output_format: Output format
        task_instance: Celery task instance for progress updates
    
    Returns:
        Dict with processing results
    """
    import time
    import librosa
    import soundfile as sf
    from pathlib import Path
    
    start_time = time.time()
    
    # Create output directory
    output_dir = Path(settings.upload_dir) / "processed"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Generate output filename
    input_file = Path(input_path)
    output_filename = f"{input_file.stem}_processed.{output_format}"
    output_path = output_dir / output_filename
    
    # Update progress
    task_instance.update_state(
        state="PROGRESS",
        meta={"current": 10, "total": 100, "status": "Loading audio file..."}
    )
    
    # Load audio file
    audio_data, sample_rate = librosa.load(input_path, sr=None)
    
    # Update progress
    task_instance.update_state(
        state="PROGRESS",
        meta={"current": 30, "total": 100, "status": "Applying effects..."}
    )
    
    # Apply effects based on configuration
    effects_applied = []
    
    # Voice enhancement
    if effects_config.get("voice_enhancement", {}).get("enabled", False):
        audio_data = _apply_voice_enhancement(audio_data, sample_rate)
        effects_applied.append("voice_enhancement")
    
    # Background music mixing
    if effects_config.get("background_music", {}).get("enabled", False):
        audio_data = _apply_background_music(
            audio_data, 
            effects_config["background_music"]
        )
        effects_applied.append("background_music")
    
    # Sound effects
    if effects_config.get("sound_effects", {}).get("enabled", False):
        audio_data = _apply_sound_effects(
            audio_data,
            effects_config["sound_effects"]
        )
        effects_applied.append("sound_effects")
    
    # Update progress
    task_instance.update_state(
        state="PROGRESS",
        meta={"current": 80, "total": 100, "status": "Saving processed audio..."}
    )
    
    # Save processed audio
    sf.write(str(output_path), audio_data, sample_rate)
    
    # Update progress
    task_instance.update_state(
        state="PROGRESS",
        meta={"current": 100, "total": 100, "status": "Processing complete!"}
    )
    
    processing_time = time.time() - start_time
    
    return {
        "output_path": str(output_path),
        "processing_time": processing_time,
        "effects_applied": effects_applied
    }


def _apply_voice_enhancement(audio_data, sample_rate):
    """Apply voice enhancement effects"""
    import librosa
    
    # Noise reduction (simple high-pass filter)
    audio_data = librosa.effects.preemphasis(audio_data)
    
    # Normalize audio
    audio_data = librosa.util.normalize(audio_data)
    
    return audio_data


def _apply_background_music(audio_data, config):
    """Apply background music mixing"""
    # This is a placeholder implementation
    # In a real implementation, you would load and mix background music
    return audio_data


def _apply_sound_effects(audio_data, config):
    """Apply sound effects"""
    # This is a placeholder implementation
    # In a real implementation, you would apply various sound effects
    return audio_data


@celery_app.task(name="cleanup_temp_files")
def cleanup_temp_files(file_paths: list) -> Dict[str, Any]:
    """
    Clean up temporary files
    
    Args:
        file_paths: List of file paths to clean up
    
    Returns:
        Dict with cleanup results
    """
    cleaned_files = []
    errors = []
    
    for file_path in file_paths:
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
                cleaned_files.append(file_path)
        except Exception as e:
            errors.append(f"Failed to delete {file_path}: {str(e)}")
    
    return {
        "cleaned_files": cleaned_files,
        "errors": errors,
        "total_cleaned": len(cleaned_files)
    }
