"""
Audio processing API endpoints
"""

import os
import tempfile
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Query
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from pathlib import Path

from ....database import get_db
from ....models import AudioFile, Project, User, ProcessingJob, JobStatus
from ....schemas import (
    AudioFile as AudioFileSchema,
    AudioFileCreate,
    AudioUploadResponse,
    ProcessingJob as ProcessingJobSchema,
    ProcessingJobCreate,
    ProcessingJobResponse
)
from ....tasks.audio_processing import process_audio_file
from ....tasks.whisperx_tasks import transcribe_audio, diarize_speakers
from ....config import settings
from ...dependencies import get_current_active_user

router = APIRouter()


@router.get("/files", response_model=List[AudioFileSchema])
def get_audio_files(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    project_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Get list of audio files
    
    Args:
        skip: Number of files to skip
        limit: Maximum number of files to return
        project_id: Filter by project ID
        db: Database session
        current_user: Current authenticated user
    
    Returns:
        List of audio files
    """
    query = db.query(AudioFile)
    
    if project_id:
        query = query.filter(AudioFile.project_id == project_id)
    
    audio_files = query.offset(skip).limit(limit).all()
    return audio_files


@router.post("/upload", response_model=AudioUploadResponse)
async def upload_audio_file(
    file: UploadFile = File(...),
    project_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Upload audio file
    
    Args:
        file: Audio file to upload
        project_id: Project ID to associate with
        db: Database session
        current_user: Current authenticated user
    
    Returns:
        Upload response with file details
    """
    # Validate file type
    file_extension = Path(file.filename).suffix.lower()
    if file_extension not in settings.allowed_audio_formats:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file format. Allowed formats: {', '.join(settings.allowed_audio_formats)}"
        )
    
    # Validate file size
    file_content = await file.read()
    if len(file_content) > settings.max_file_size:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File too large. Maximum size: {settings.max_file_size / (1024*1024):.1f}MB"
        )
    
    # Create upload directory
    upload_dir = Path(settings.upload_dir)
    upload_dir.mkdir(parents=True, exist_ok=True)
    
    # Generate unique filename
    import uuid
    file_id = str(uuid.uuid4())
    filename = f"{file_id}{file_extension}"
    file_path = upload_dir / filename
    
    # Save file
    with open(file_path, "wb") as buffer:
        buffer.write(file_content)
    
    # Get audio metadata
    try:
        import librosa
        audio_data, sample_rate = librosa.load(str(file_path), sr=None)
        duration = len(audio_data) / sample_rate
        channels = 1 if len(audio_data.shape) == 1 else audio_data.shape[1]
    except Exception:
        duration = None
        sample_rate = None
        channels = None
    
    # Create database record
    audio_file = AudioFile(
        filename=filename,
        original_filename=file.filename,
        file_path=str(file_path),
        file_size=len(file_content),
        duration=duration,
        format=file_extension[1:],  # Remove dot
        sample_rate=sample_rate,
        channels=channels,
        project_id=project_id
    )
    
    db.add(audio_file)
    db.commit()
    db.refresh(audio_file)
    
    return AudioUploadResponse(
        file_id=audio_file.id,
        filename=audio_file.filename,
        file_size=audio_file.file_size,
        duration=audio_file.duration,
        message="File uploaded successfully"
    )


@router.get("/files/{file_id}", response_model=AudioFileSchema)
def get_audio_file(
    file_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Get audio file by ID
    
    Args:
        file_id: Audio file ID
        db: Database session
        current_user: Current authenticated user
    
    Returns:
        Audio file details
    """
    audio_file = db.query(AudioFile).filter(AudioFile.id == file_id).first()
    if not audio_file:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Audio file not found"
        )
    
    return audio_file


@router.get("/files/{file_id}/download")
def download_audio_file(
    file_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Download audio file
    
    Args:
        file_id: Audio file ID
        db: Database session
        current_user: Current authenticated user
    
    Returns:
        File response
    """
    audio_file = db.query(AudioFile).filter(AudioFile.id == file_id).first()
    if not audio_file:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Audio file not found"
        )
    
    if not os.path.exists(audio_file.file_path):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Audio file not found on disk"
        )
    
    return FileResponse(
        path=audio_file.file_path,
        filename=audio_file.original_filename,
        media_type="audio/*"
    )


@router.post("/process", response_model=ProcessingJobResponse)
def process_audio(
    job_data: ProcessingJobCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Start audio processing job
    
    Args:
        job_data: Processing job configuration
        db: Database session
        current_user: Current authenticated user
    
    Returns:
        Processing job response
    """
    # Verify audio file exists
    audio_file = db.query(AudioFile).filter(AudioFile.id == job_data.audio_file_id).first()
    if not audio_file:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Audio file not found"
        )
    
    # Create processing job
    processing_job = ProcessingJob(
        name=job_data.name,
        description=job_data.description,
        effects_config=job_data.effects_config,
        output_format=job_data.output_format,
        audio_file_id=job_data.audio_file_id,
        project_id=job_data.project_id,
        status=JobStatus.PENDING
    )
    
    db.add(processing_job)
    db.commit()
    db.refresh(processing_job)
    
    # Start Celery task
    task = process_audio_file.delay(
        processing_job.id,
        job_data.audio_file_id,
        job_data.effects_config or {},
        job_data.output_format.value
    )
    
    return ProcessingJobResponse(
        job_id=processing_job.id,
        status=processing_job.status,
        progress=processing_job.progress,
        message="Processing job started"
    )


@router.get("/jobs", response_model=List[ProcessingJobSchema])
def get_processing_jobs(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    project_id: Optional[int] = Query(None),
    status_filter: Optional[JobStatus] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Get list of processing jobs
    
    Args:
        skip: Number of jobs to skip
        limit: Maximum number of jobs to return
        project_id: Filter by project ID
        status_filter: Filter by job status
        db: Database session
        current_user: Current authenticated user
    
    Returns:
        List of processing jobs
    """
    query = db.query(ProcessingJob)
    
    if project_id:
        query = query.filter(ProcessingJob.project_id == project_id)
    
    if status_filter:
        query = query.filter(ProcessingJob.status == status_filter)
    
    jobs = query.offset(skip).limit(limit).all()
    return jobs


@router.get("/jobs/{job_id}", response_model=ProcessingJobSchema)
def get_processing_job(
    job_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Get processing job by ID
    
    Args:
        job_id: Processing job ID
        db: Database session
        current_user: Current authenticated user
    
    Returns:
        Processing job details
    """
    job = db.query(ProcessingJob).filter(ProcessingJob.id == job_id).first()
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Processing job not found"
        )
    
    return job


@router.post("/transcribe/{file_id}")
def transcribe_audio_file(
    file_id: int,
    language: Optional[str] = None,
    model_size: str = "base",
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Transcribe audio file using WhisperX
    
    Args:
        file_id: Audio file ID
        language: Language code (optional)
        model_size: Whisper model size
        db: Database session
        current_user: Current authenticated user
    
    Returns:
        Transcription task response
    """
    # Verify audio file exists
    audio_file = db.query(AudioFile).filter(AudioFile.id == file_id).first()
    if not audio_file:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Audio file not found"
        )
    
    # Start transcription task
    task = transcribe_audio.delay(file_id, language, model_size)
    
    return {
        "task_id": task.id,
        "status": "started",
        "message": "Transcription task started"
    }


@router.post("/diarize/{file_id}")
def diarize_audio_file(
    file_id: int,
    transcription_result: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Perform speaker diarization on audio file
    
    Args:
        file_id: Audio file ID
        transcription_result: Previous transcription result
        db: Database session
        current_user: Current authenticated user
    
    Returns:
        Diarization task response
    """
    # Verify audio file exists
    audio_file = db.query(AudioFile).filter(AudioFile.id == file_id).first()
    if not audio_file:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Audio file not found"
        )
    
    # Start diarization task
    task = diarize_speakers.delay(file_id, transcription_result)
    
    return {
        "task_id": task.id,
        "status": "started",
        "message": "Diarization task started"
    }
