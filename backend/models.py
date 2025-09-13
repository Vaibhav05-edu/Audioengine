"""
Database models for the Audio Drama FX Engine
"""

from datetime import datetime
from enum import Enum
from typing import Optional
from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, Float, ForeignKey, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from .database import Base


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


class Project(Base):
    """Project model"""
    __tablename__ = "projects"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, index=True)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    is_active = Column(Boolean, default=True)
    
    # Relationships
    audio_files = relationship("AudioFile", back_populates="project")
    processing_jobs = relationship("ProcessingJob", back_populates="project")
    scenes = relationship("Scene", back_populates="project")
    fx_plans = relationship("FXPlan", back_populates="project")
    assets = relationship("Asset", back_populates="project")
    renders = relationship("Render", back_populates="project")


class AudioFile(Base):
    """Audio file model"""
    __tablename__ = "audio_files"
    
    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String(255), nullable=False)
    original_filename = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=False)
    file_size = Column(Integer, nullable=False)
    duration = Column(Float, nullable=True)  # Duration in seconds
    format = Column(String(10), nullable=False)
    sample_rate = Column(Integer, nullable=True)
    channels = Column(Integer, nullable=True)
    bit_rate = Column(Integer, nullable=True)
    
    # Metadata
    metadata = Column(JSON, nullable=True)
    
    # Timestamps
    uploaded_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Foreign keys
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=True)
    
    # Relationships
    project = relationship("Project", back_populates="audio_files")
    processing_jobs = relationship("ProcessingJob", back_populates="audio_file")


class ProcessingJob(Base):
    """Audio processing job model"""
    __tablename__ = "processing_jobs"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    status = Column(String(20), default=JobStatus.PENDING, index=True)
    
    # Processing configuration
    effects_config = Column(JSON, nullable=True)
    output_format = Column(String(10), default=AudioFormat.WAV)
    output_path = Column(String(500), nullable=True)
    
    # Progress tracking
    progress = Column(Float, default=0.0)  # 0.0 to 1.0
    current_step = Column(String(100), nullable=True)
    error_message = Column(Text, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    
    # Foreign keys
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=True)
    audio_file_id = Column(Integer, ForeignKey("audio_files.id"), nullable=True)
    
    # Relationships
    project = relationship("Project", back_populates="processing_jobs")
    audio_file = relationship("AudioFile", back_populates="processing_jobs")


class Effect(Base):
    """Audio effect model"""
    __tablename__ = "effects"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, unique=True)
    display_name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    category = Column(String(50), nullable=True)
    
    # Effect configuration
    parameters = Column(JSON, nullable=True)
    is_enabled = Column(Boolean, default=True)
    is_builtin = Column(Boolean, default=False)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


class User(Base):
    """User model for authentication"""
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), nullable=False, unique=True, index=True)
    email = Column(String(100), nullable=False, unique=True, index=True)
    hashed_password = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True)
    is_superuser = Column(Boolean, default=False)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    last_login = Column(DateTime(timezone=True), nullable=True)


class Scene(Base):
    """Scene model for audio drama scenes"""
    __tablename__ = "scenes"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, index=True)
    description = Column(Text, nullable=True)
    
    # Scene metadata
    scene_number = Column(Integer, nullable=True)
    duration = Column(Float, nullable=True)  # Duration in seconds
    location = Column(String(255), nullable=True)
    time_of_day = Column(String(50), nullable=True)
    mood = Column(String(100), nullable=True)
    
    # Timeline JSON - stored exactly as specified in PRD
    timeline_json = Column(JSON, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Foreign keys
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    
    # Relationships
    project = relationship("Project", back_populates="scenes")
    fx_plans = relationship("FXPlan", back_populates="scene")
    assets = relationship("Asset", back_populates="scene")
    renders = relationship("Render", back_populates="scene")


class FXPlan(Base):
    """FX Plan model for scene effects planning"""
    __tablename__ = "fx_plans"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, index=True)
    description = Column(Text, nullable=True)
    
    # Plan status
    status = Column(String(20), default=JobStatus.PENDING, index=True)
    
    # FX Plan configuration
    effects_config = Column(JSON, nullable=True)  # Detailed effects configuration
    priority = Column(Integer, default=0)  # Processing priority
    estimated_duration = Column(Float, nullable=True)  # Estimated processing time
    
    # Progress tracking
    progress = Column(Float, default=0.0)  # 0.0 to 1.0
    current_step = Column(String(100), nullable=True)
    error_message = Column(Text, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    
    # Foreign keys
    scene_id = Column(Integer, ForeignKey("scenes.id"), nullable=False)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    
    # Relationships
    scene = relationship("Scene", back_populates="fx_plans")
    project = relationship("Project", back_populates="fx_plans")
    renders = relationship("Render", back_populates="fx_plan")


class Asset(Base):
    """Asset model for audio assets (dialogue, music, SFX)"""
    __tablename__ = "assets"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, index=True)
    description = Column(Text, nullable=True)
    
    # Asset metadata
    asset_type = Column(String(50), nullable=False)  # dialogue, music, sfx, ambience
    file_path = Column(String(500), nullable=False)
    original_filename = Column(String(255), nullable=False)
    file_size = Column(Integer, nullable=False)
    duration = Column(Float, nullable=True)  # Duration in seconds
    format = Column(String(10), nullable=False)
    sample_rate = Column(Integer, nullable=True)
    channels = Column(Integer, nullable=True)
    bit_rate = Column(Integer, nullable=True)
    
    # Asset properties
    volume = Column(Float, default=1.0)  # Volume level (0.0 to 1.0)
    pan = Column(Float, default=0.0)  # Pan position (-1.0 to 1.0)
    loop = Column(Boolean, default=False)  # Whether asset should loop
    fade_in = Column(Float, default=0.0)  # Fade in duration in seconds
    fade_out = Column(Float, default=0.0)  # Fade out duration in seconds
    
    # Timeline position
    start_time = Column(Float, default=0.0)  # Start time in scene timeline
    end_time = Column(Float, nullable=True)  # End time in scene timeline
    
    # Additional metadata
    metadata = Column(JSON, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Foreign keys
    scene_id = Column(Integer, ForeignKey("scenes.id"), nullable=False)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    
    # Relationships
    scene = relationship("Scene", back_populates="assets")
    project = relationship("Project", back_populates="assets")


class Render(Base):
    """Render model for processed audio outputs"""
    __tablename__ = "renders"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, index=True)
    description = Column(Text, nullable=True)
    
    # Render configuration
    render_type = Column(String(50), nullable=False)  # stems, final_mix, preview
    output_format = Column(String(10), default=AudioFormat.WAV)
    sample_rate = Column(Integer, nullable=True)
    bit_depth = Column(Integer, nullable=True)
    channels = Column(Integer, nullable=True)
    
    # Render status
    status = Column(String(20), default=JobStatus.PENDING, index=True)
    
    # Output files
    output_path = Column(String(500), nullable=True)
    file_size = Column(Integer, nullable=True)
    duration = Column(Float, nullable=True)  # Duration in seconds
    
    # Progress tracking
    progress = Column(Float, default=0.0)  # 0.0 to 1.0
    current_step = Column(String(100), nullable=True)
    error_message = Column(Text, nullable=True)
    
    # Render settings
    render_settings = Column(JSON, nullable=True)  # Detailed render configuration
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    
    # Foreign keys
    scene_id = Column(Integer, ForeignKey("scenes.id"), nullable=False)
    fx_plan_id = Column(Integer, ForeignKey("fx_plans.id"), nullable=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    
    # Relationships
    scene = relationship("Scene", back_populates="renders")
    fx_plan = relationship("FXPlan", back_populates="renders")
    project = relationship("Project", back_populates="renders")
