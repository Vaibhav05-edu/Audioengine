"""
Tests for database models
"""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from backend.database import Base
from backend.models import Project, AudioFile, ProcessingJob, Effect, User


@pytest.fixture
def db_session():
    """Create test database session"""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = SessionLocal()
    yield session
    session.close()


def test_project_creation(db_session):
    """Test project creation"""
    project = Project(
        name="Test Project",
        description="A test project"
    )
    db_session.add(project)
    db_session.commit()
    
    assert project.id is not None
    assert project.name == "Test Project"
    assert project.is_active is True


def test_audio_file_creation(db_session):
    """Test audio file creation"""
    audio_file = AudioFile(
        filename="test.wav",
        original_filename="test.wav",
        file_path="/path/to/test.wav",
        file_size=1024,
        format="wav"
    )
    db_session.add(audio_file)
    db_session.commit()
    
    assert audio_file.id is not None
    assert audio_file.filename == "test.wav"
    assert audio_file.format == "wav"


def test_processing_job_creation(db_session):
    """Test processing job creation"""
    job = ProcessingJob(
        name="Test Job",
        description="A test processing job"
    )
    db_session.add(job)
    db_session.commit()
    
    assert job.id is not None
    assert job.name == "Test Job"
    assert job.status == "pending"
    assert job.progress == 0.0


def test_effect_creation(db_session):
    """Test effect creation"""
    effect = Effect(
        name="test_effect",
        display_name="Test Effect",
        description="A test effect"
    )
    db_session.add(effect)
    db_session.commit()
    
    assert effect.id is not None
    assert effect.name == "test_effect"
    assert effect.is_enabled is True
    assert effect.is_builtin is False


def test_user_creation(db_session):
    """Test user creation"""
    user = User(
        username="testuser",
        email="test@example.com",
        hashed_password="hashed_password"
    )
    db_session.add(user)
    db_session.commit()
    
    assert user.id is not None
    assert user.username == "testuser"
    assert user.is_active is True
    assert user.is_superuser is False
