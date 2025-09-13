"""
WhisperX integration tasks
"""

from typing import Dict, Any, Optional
from celery import current_task
from sqlalchemy.orm import Session

from ..celery_app import celery_app
from ..database import SessionLocal
from ..models import ProcessingJob, JobStatus, AudioFile


@celery_app.task(bind=True, name="transcribe_audio")
def transcribe_audio(
    self,
    audio_file_id: int,
    language: Optional[str] = None,
    model_size: str = "base"
) -> Dict[str, Any]:
    """
    Transcribe audio using WhisperX
    
    Args:
        audio_file_id: Audio file ID
        language: Language code (optional, auto-detect if None)
        model_size: Whisper model size (tiny, base, small, medium, large)
    
    Returns:
        Dict with transcription results
    """
    db = SessionLocal()
    try:
        # Get the audio file
        audio_file = db.query(AudioFile).filter(AudioFile.id == audio_file_id).first()
        if not audio_file:
            raise ValueError(f"Audio file {audio_file_id} not found")
        
        # Update progress
        self.update_state(
            state="PROGRESS",
            meta={"current": 0, "total": 100, "status": "Starting transcription..."}
        )
        
        # Perform transcription
        result = _perform_whisperx_transcription(
            audio_file.file_path,
            language,
            model_size,
            self
        )
        
        return {
            "audio_file_id": audio_file_id,
            "status": "completed",
            "transcription": result["transcription"],
            "segments": result["segments"],
            "language": result["language"],
            "processing_time": result["processing_time"]
        }
        
    except Exception as e:
        # Re-raise the exception
        raise
    finally:
        db.close()


def _perform_whisperx_transcription(
    audio_path: str,
    language: Optional[str],
    model_size: str,
    task_instance
) -> Dict[str, Any]:
    """
    Internal function to perform WhisperX transcription
    
    Args:
        audio_path: Path to audio file
        language: Language code
        model_size: Model size
        task_instance: Celery task instance for progress updates
    
    Returns:
        Dict with transcription results
    """
    import time
    import whisperx
    import torch
    
    start_time = time.time()
    
    # Update progress
    task_instance.update_state(
        state="PROGRESS",
        meta={"current": 10, "total": 100, "status": "Loading WhisperX model..."}
    )
    
    # Load WhisperX model
    device = "cuda" if torch.cuda.is_available() else "cpu"
    model = whisperx.load_model(model_size, device=device, language=language)
    
    # Update progress
    task_instance.update_state(
        state="PROGRESS",
        meta={"current": 30, "total": 100, "status": "Transcribing audio..."}
    )
    
    # Transcribe audio
    result = model.transcribe(audio_path)
    
    # Update progress
    task_instance.update_state(
        state="PROGRESS",
        meta={"current": 70, "total": 100, "status": "Processing segments..."}
    )
    
    # Process segments
    segments = []
    for segment in result["segments"]:
        segments.append({
            "start": segment["start"],
            "end": segment["end"],
            "text": segment["text"],
            "words": segment.get("words", [])
        })
    
    # Update progress
    task_instance.update_state(
        state="PROGRESS",
        meta={"current": 100, "total": 100, "status": "Transcription complete!"}
    )
    
    processing_time = time.time() - start_time
    
    return {
        "transcription": result["text"],
        "segments": segments,
        "language": result["language"],
        "processing_time": processing_time
    }


@celery_app.task(bind=True, name="diarize_speakers")
def diarize_speakers(
    self,
    audio_file_id: int,
    transcription_result: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Perform speaker diarization using WhisperX
    
    Args:
        audio_file_id: Audio file ID
        transcription_result: Previous transcription result
    
    Returns:
        Dict with diarization results
    """
    db = SessionLocal()
    try:
        # Get the audio file
        audio_file = db.query(AudioFile).filter(AudioFile.id == audio_file_id).first()
        if not audio_file:
            raise ValueError(f"Audio file {audio_file_id} not found")
        
        # Update progress
        self.update_state(
            state="PROGRESS",
        meta={"current": 0, "total": 100, "status": "Starting speaker diarization..."}
        )
        
        # Perform diarization
        result = _perform_speaker_diarization(
            audio_file.file_path,
            transcription_result,
            self
        )
        
        return {
            "audio_file_id": audio_file_id,
            "status": "completed",
            "speakers": result["speakers"],
            "segments": result["segments"],
            "processing_time": result["processing_time"]
        }
        
    except Exception as e:
        # Re-raise the exception
        raise
    finally:
        db.close()


def _perform_speaker_diarization(
    audio_path: str,
    transcription_result: Dict[str, Any],
    task_instance
) -> Dict[str, Any]:
    """
    Internal function to perform speaker diarization
    
    Args:
        audio_path: Path to audio file
        transcription_result: Transcription result
        task_instance: Celery task instance for progress updates
    
    Returns:
        Dict with diarization results
    """
    import time
    import whisperx
    import torch
    
    start_time = time.time()
    
    # Update progress
    task_instance.update_state(
        state="PROGRESS",
        meta={"current": 20, "total": 100, "status": "Loading diarization model..."}
    )
    
    # Load diarization model
    device = "cuda" if torch.cuda.is_available() else "cpu"
    diarize_model = whisperx.DiarizationPipeline(use_auth_token=None, device=device)
    
    # Update progress
    task_instance.update_state(
        state="PROGRESS",
        meta={"current": 50, "total": 100, "status": "Performing diarization..."}
    )
    
    # Perform diarization
    diarize_segments = diarize_model(audio_path)
    
    # Update progress
    task_instance.update_state(
        state="PROGRESS",
        meta={"current": 80, "total": 100, "status": "Processing results..."}
    )
    
    # Process results
    speakers = list(set([segment["speaker"] for segment in diarize_segments]))
    segments = []
    
    for segment in diarize_segments:
        segments.append({
            "start": segment["start"],
            "end": segment["end"],
            "speaker": segment["speaker"],
            "text": segment.get("text", "")
        })
    
    # Update progress
    task_instance.update_state(
        state="PROGRESS",
        meta={"current": 100, "total": 100, "status": "Diarization complete!"}
    )
    
    processing_time = time.time() - start_time
    
    return {
        "speakers": speakers,
        "segments": segments,
        "processing_time": processing_time
    }
