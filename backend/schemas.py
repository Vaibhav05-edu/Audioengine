"""
Pydantic schemas for the Audio Drama FX Engine
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, validator


class JobStatus(str, Enum):
    """Job status enumeration"""

    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class AudioFormat(str, Enum):
    """Audio format enumeration"""

    WAV = "wav"
    MP3 = "mp3"
    FLAC = "flac"
    M4A = "m4a"
    AAC = "aac"
    OGG = "ogg"


# Base schemas
class BaseSchema(BaseModel):
    """Base schema with common fields"""

    class Config:
        from_attributes = True


# Project schemas
class ProjectBase(BaseSchema):
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None


class ProjectCreate(ProjectBase):
    pass


class ProjectUpdate(BaseSchema):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    is_active: Optional[bool] = None


class Project(ProjectBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime]
    is_active: bool


# Audio file schemas
class AudioFileBase(BaseSchema):
    filename: str = Field(..., min_length=1, max_length=255)
    original_filename: str = Field(..., min_length=1, max_length=255)
    file_size: int = Field(..., gt=0)
    duration: Optional[float] = Field(None, ge=0)
    format: AudioFormat
    sample_rate: Optional[int] = Field(None, gt=0)
    channels: Optional[int] = Field(None, gt=0)
    bit_rate: Optional[int] = Field(None, gt=0)
    metadata: Optional[Dict[str, Any]] = None


class AudioFileCreate(AudioFileBase):
    file_path: str = Field(..., min_length=1)
    project_id: Optional[int] = None


class AudioFileUpdate(BaseSchema):
    filename: Optional[str] = Field(None, min_length=1, max_length=255)
    metadata: Optional[Dict[str, Any]] = None


class AudioFile(AudioFileBase):
    id: int
    file_path: str
    uploaded_at: datetime
    project_id: Optional[int]


# Processing job schemas
class ProcessingJobBase(BaseSchema):
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    effects_config: Optional[Dict[str, Any]] = None
    output_format: AudioFormat = AudioFormat.WAV


class ProcessingJobCreate(ProcessingJobBase):
    audio_file_id: int
    project_id: Optional[int] = None


class ProcessingJobUpdate(BaseSchema):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    effects_config: Optional[Dict[str, Any]] = None
    output_format: Optional[AudioFormat] = None


class ProcessingJob(ProcessingJobBase):
    id: int
    status: JobStatus
    progress: float = Field(..., ge=0, le=1)
    current_step: Optional[str] = None
    error_message: Optional[str] = None
    output_path: Optional[str] = None
    created_at: datetime
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    project_id: Optional[int]
    audio_file_id: Optional[int]


# Effect schemas
class EffectBase(BaseSchema):
    name: str = Field(..., min_length=1, max_length=100)
    display_name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    category: Optional[str] = Field(None, max_length=50)
    parameters: Optional[Dict[str, Any]] = None


class EffectCreate(EffectBase):
    is_enabled: bool = True


class EffectUpdate(BaseSchema):
    display_name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    category: Optional[str] = Field(None, max_length=50)
    parameters: Optional[Dict[str, Any]] = None
    is_enabled: Optional[bool] = None


class Effect(EffectBase):
    id: int
    is_enabled: bool
    is_builtin: bool
    created_at: datetime
    updated_at: Optional[datetime]


# User schemas
class UserBase(BaseSchema):
    username: str = Field(..., min_length=3, max_length=50)
    email: str = Field(..., regex=r"^[^@]+@[^@]+\.[^@]+$")


class UserCreate(UserBase):
    password: str = Field(..., min_length=8)


class UserUpdate(BaseSchema):
    username: Optional[str] = Field(None, min_length=3, max_length=50)
    email: Optional[str] = Field(None, regex=r"^[^@]+@[^@]+\.[^@]+$")
    password: Optional[str] = Field(None, min_length=8)
    is_active: Optional[bool] = None


class User(UserBase):
    id: int
    is_active: bool
    is_superuser: bool
    created_at: datetime
    last_login: Optional[datetime]


# Authentication schemas
class Token(BaseSchema):
    access_token: str
    token_type: str


class TokenData(BaseSchema):
    username: Optional[str] = None


# API response schemas
class APIResponse(BaseSchema):
    success: bool = True
    message: str
    data: Optional[Dict[str, Any]] = None


class PaginatedResponse(BaseSchema):
    items: List[Any]
    total: int
    page: int
    size: int
    pages: int


# Audio processing schemas
class AudioUploadResponse(BaseSchema):
    file_id: int
    filename: str
    file_size: int
    duration: Optional[float]
    message: str


class ProcessingJobResponse(BaseSchema):
    job_id: int
    status: JobStatus
    progress: float
    message: str


class TranscriptionResult(BaseSchema):
    text: str
    segments: List[Dict[str, Any]]
    language: str
    confidence: Optional[float] = None


class DiarizationResult(BaseSchema):
    speakers: List[str]
    segments: List[Dict[str, Any]]
    speaker_count: int


# Health check schemas
class HealthCheck(BaseSchema):
    status: str
    service: str
    timestamp: datetime
    version: str
    environment: str


# Error schemas
class ErrorResponse(BaseSchema):
    error: str
    message: str
    details: Optional[Dict[str, Any]] = None


# Scene schemas
class SceneBase(BaseSchema):
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    scene_number: Optional[int] = Field(None, ge=1)
    duration: Optional[float] = Field(None, ge=0)
    location: Optional[str] = Field(None, max_length=255)
    time_of_day: Optional[str] = Field(None, max_length=50)
    mood: Optional[str] = Field(None, max_length=100)
    timeline_json: Optional[Dict[str, Any]] = None


class SceneCreate(SceneBase):
    project_id: int


class SceneUpdate(BaseSchema):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    scene_number: Optional[int] = Field(None, ge=1)
    duration: Optional[float] = Field(None, ge=0)
    location: Optional[str] = Field(None, max_length=255)
    time_of_day: Optional[str] = Field(None, max_length=50)
    mood: Optional[str] = Field(None, max_length=100)
    timeline_json: Optional[Dict[str, Any]] = None


class Scene(SceneBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime]
    project_id: int


# FXPlan schemas
class FXPlanBase(BaseSchema):
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    effects_config: Optional[Dict[str, Any]] = None
    priority: int = Field(default=0)
    estimated_duration: Optional[float] = Field(None, ge=0)


class FXPlanCreate(FXPlanBase):
    scene_id: int
    project_id: int


class FXPlanUpdate(BaseSchema):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    effects_config: Optional[Dict[str, Any]] = None
    priority: Optional[int] = None
    estimated_duration: Optional[float] = Field(None, ge=0)


class FXPlan(FXPlanBase):
    id: int
    status: JobStatus
    progress: float = Field(..., ge=0, le=1)
    current_step: Optional[str] = None
    error_message: Optional[str] = None
    created_at: datetime
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    scene_id: int
    project_id: int


# Asset schemas
class AssetBase(BaseSchema):
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    asset_type: str = Field(..., regex=r"^(dialogue|music|sfx|ambience)$")
    file_size: int = Field(..., gt=0)
    duration: Optional[float] = Field(None, ge=0)
    format: AudioFormat
    sample_rate: Optional[int] = Field(None, gt=0)
    channels: Optional[int] = Field(None, gt=0)
    bit_rate: Optional[int] = Field(None, gt=0)
    volume: float = Field(default=1.0, ge=0.0, le=1.0)
    pan: float = Field(default=0.0, ge=-1.0, le=1.0)
    loop: bool = Field(default=False)
    fade_in: float = Field(default=0.0, ge=0)
    fade_out: float = Field(default=0.0, ge=0)
    start_time: float = Field(default=0.0, ge=0)
    end_time: Optional[float] = Field(None, ge=0)
    metadata: Optional[Dict[str, Any]] = None


class AssetCreate(AssetBase):
    file_path: str = Field(..., min_length=1)
    original_filename: str = Field(..., min_length=1, max_length=255)
    scene_id: int
    project_id: int


class AssetUpdate(BaseSchema):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    volume: Optional[float] = Field(None, ge=0.0, le=1.0)
    pan: Optional[float] = Field(None, ge=-1.0, le=1.0)
    loop: Optional[bool] = None
    fade_in: Optional[float] = Field(None, ge=0)
    fade_out: Optional[float] = Field(None, ge=0)
    start_time: Optional[float] = Field(None, ge=0)
    end_time: Optional[float] = Field(None, ge=0)
    metadata: Optional[Dict[str, Any]] = None


class Asset(AssetBase):
    id: int
    file_path: str
    original_filename: str
    created_at: datetime
    updated_at: Optional[datetime]
    scene_id: int
    project_id: int


# Render schemas
class RenderBase(BaseSchema):
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    render_type: str = Field(..., regex=r"^(stems|final_mix|preview)$")
    output_format: AudioFormat = AudioFormat.WAV
    sample_rate: Optional[int] = Field(None, gt=0)
    bit_depth: Optional[int] = Field(None, gt=0)
    channels: Optional[int] = Field(None, gt=0)
    render_settings: Optional[Dict[str, Any]] = None


class RenderCreate(RenderBase):
    scene_id: int
    project_id: int
    fx_plan_id: Optional[int] = None


class RenderUpdate(BaseSchema):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    render_settings: Optional[Dict[str, Any]] = None


class Render(RenderBase):
    id: int
    status: JobStatus
    progress: float = Field(..., ge=0, le=1)
    current_step: Optional[str] = None
    error_message: Optional[str] = None
    output_path: Optional[str] = None
    file_size: Optional[int] = None
    duration: Optional[float] = None
    created_at: datetime
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    scene_id: int
    fx_plan_id: Optional[int]
    project_id: int


# Timeline JSON schemas (as specified in PRD)
class TimelineTrack(BaseSchema):
    name: str
    type: str = Field(..., regex=r"^(dialogue|music|sfx|ambience)$")
    assets: List[Dict[str, Any]] = Field(default_factory=list)
    volume: float = Field(default=1.0, ge=0.0, le=1.0)
    pan: float = Field(default=0.0, ge=-1.0, le=1.0)
    mute: bool = Field(default=False)
    solo: bool = Field(default=False)


class TimelineJSON(BaseSchema):
    version: str = Field(default="1.0")
    duration: float = Field(..., ge=0)
    sample_rate: int = Field(default=44100, gt=0)
    tracks: List[TimelineTrack] = Field(default_factory=list)
    metadata: Optional[Dict[str, Any]] = None


# FX Plan schemas
class GeneratedPrompt(BaseSchema):
    prompt: str
    prompt_type: str = Field(..., regex=r"^(ambience|sfx)$")
    confidence: float = Field(..., ge=0.0, le=1.0)
    source_elements: List[str] = Field(default_factory=list)
    template_used: str
    manual_override: bool = Field(default=False)
    override_reason: Optional[str] = None


class SceneAnalysis(BaseSchema):
    scene_heading: str
    location: str
    time_of_day: str
    mood: Optional[str] = None
    verbs: List[str] = Field(default_factory=list)
    nouns: List[str] = Field(default_factory=list)
    adjectives: List[str] = Field(default_factory=list)
    action_words: List[str] = Field(default_factory=list)
    sound_cues: List[str] = Field(default_factory=list)
    environment_cues: List[str] = Field(default_factory=list)


class FXPlanPrompts(BaseSchema):
    scene_id: int
    scene_name: str
    generated_at: datetime
    ambience_prompts: List[GeneratedPrompt] = Field(default_factory=list)
    sfx_prompts: List[GeneratedPrompt] = Field(default_factory=list)
    manual_overrides: Dict[str, str] = Field(default_factory=dict)
    analysis_summary: SceneAnalysis


class FXPlanJSON(BaseSchema):
    """FX Plan JSON structure for storing generated prompts and effects configuration"""

    version: str = Field(default="1.0")
    scene_id: int
    scene_name: str
    generated_at: datetime
    last_updated: datetime

    # Generated prompts
    prompts: FXPlanPrompts

    # Effects configuration
    effects_config: Dict[str, Any] = Field(default_factory=dict)

    # Processing settings
    processing_settings: Dict[str, Any] = Field(default_factory=dict)

    # Manual overrides
    manual_overrides: Dict[str, Any] = Field(default_factory=dict)

    # Metadata
    metadata: Dict[str, Any] = Field(default_factory=dict)


# API Request/Response schemas for new endpoints
class IngestRequest(BaseSchema):
    scene_id: int
    asset_type: str = Field(..., regex=r"^(dialogue|music|sfx|ambience)$")
    file: str  # Base64 encoded file or file path
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    start_time: float = Field(default=0.0, ge=0)
    volume: float = Field(default=1.0, ge=0.0, le=1.0)
    pan: float = Field(default=0.0, ge=-1.0, le=1.0)
    loop: bool = Field(default=False)
    fade_in: float = Field(default=0.0, ge=0)
    fade_out: float = Field(default=0.0, ge=0)


class IngestResponse(BaseSchema):
    asset_id: int
    scene_id: int
    name: str
    asset_type: str
    file_size: int
    duration: Optional[float]
    message: str


class PlanFXRequest(BaseSchema):
    scene_id: int
    plan_name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    effects_config: Optional[Dict[str, Any]] = None
    priority: int = Field(default=0)


class PlanFXResponse(BaseSchema):
    fx_plan_id: int
    scene_id: int
    name: str
    status: JobStatus
    message: str


class GenFXRequest(BaseSchema):
    fx_plan_id: int
    force_regenerate: bool = Field(default=False)


class GenFXResponse(BaseSchema):
    fx_plan_id: int
    status: JobStatus
    progress: float
    message: str


class RenderStemsRequest(BaseSchema):
    scene_id: int
    fx_plan_id: Optional[int] = None
    render_name: str = Field(..., min_length=1, max_length=255)
    render_type: str = Field(default="stems", regex=r"^(stems|final_mix|preview)$")
    output_format: AudioFormat = AudioFormat.WAV
    sample_rate: int = Field(default=44100, gt=0)
    bit_depth: int = Field(default=24, gt=0)
    channels: int = Field(default=2, gt=0)
    render_settings: Optional[Dict[str, Any]] = None


class RenderStemsResponse(BaseSchema):
    render_id: int
    scene_id: int
    name: str
    render_type: str
    status: JobStatus
    progress: float
    message: str


class DownloadRequest(BaseSchema):
    render_id: int


class DownloadResponse(BaseSchema):
    render_id: int
    filename: str
    file_size: int
    download_url: str
    expires_at: datetime
