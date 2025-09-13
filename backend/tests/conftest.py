"""
Pytest configuration and fixtures
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from backend.main import app
from backend.database import Base, get_db
from backend.models import Project, AudioFile, ProcessingJob, Effect, User, Scene, Asset, FXPlan, Render


# Test database
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="session")
def db_engine():
    """Create test database engine"""
    Base.metadata.create_all(bind=engine)
    yield engine
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def db_session(db_engine):
    """Create test database session"""
    connection = db_engine.connect()
    transaction = connection.begin()
    session = TestingSessionLocal(bind=connection)
    
    yield session
    
    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture
def client(db_session):
    """Create test client with database session"""
    def override_get_db():
        try:
            yield db_session
        finally:
            pass
    
    app.dependency_overrides[get_db] = override_get_db
    yield TestClient(app)
    app.dependency_overrides.clear()


@pytest.fixture
def sample_project(db_session):
    """Create sample project"""
    project = Project(
        name="Sample Project",
        description="A sample project for testing"
    )
    db_session.add(project)
    db_session.commit()
    db_session.refresh(project)
    return project


@pytest.fixture
def sample_audio_file(db_session, sample_project):
    """Create sample audio file"""
    audio_file = AudioFile(
        filename="sample.wav",
        original_filename="sample.wav",
        file_path="/path/to/sample.wav",
        file_size=2048,
        format="wav",
        project_id=sample_project.id
    )
    db_session.add(audio_file)
    db_session.commit()
    db_session.refresh(audio_file)
    return audio_file


@pytest.fixture
def sample_processing_job(db_session, sample_project, sample_audio_file):
    """Create sample processing job"""
    job = ProcessingJob(
        name="Sample Job",
        description="A sample processing job",
        audio_file_id=sample_audio_file.id,
        project_id=sample_project.id
    )
    db_session.add(job)
    db_session.commit()
    db_session.refresh(job)
    return job


@pytest.fixture
def sample_scene(db_session, sample_project):
    """Create sample scene"""
    scene = Scene(
        name="Sample Scene",
        description="A sample scene for testing",
        scene_number=1,
        duration=120.0,
        location="Living Room",
        time_of_day="Evening",
        mood="Dramatic",
        project_id=sample_project.id,
        timeline_json={
            "version": "1.0",
            "duration": 120.0,
            "sample_rate": 44100,
            "tracks": [],
            "metadata": {}
        }
    )
    db_session.add(scene)
    db_session.commit()
    db_session.refresh(scene)
    return scene


@pytest.fixture
def sample_asset(db_session, sample_scene, sample_project):
    """Create sample asset"""
    asset = Asset(
        name="Sample Dialogue",
        description="A sample dialogue asset",
        asset_type="dialogue",
        file_path="/path/to/sample.wav",
        original_filename="sample.wav",
        file_size=1024000,
        duration=30.0,
        format="wav",
        sample_rate=44100,
        channels=2,
        volume=1.0,
        pan=0.0,
        start_time=0.0,
        end_time=30.0,
        scene_id=sample_scene.id,
        project_id=sample_project.id
    )
    db_session.add(asset)
    db_session.commit()
    db_session.refresh(asset)
    return asset


@pytest.fixture
def sample_fx_plan(db_session, sample_scene, sample_project):
    """Create sample FX plan"""
    fx_plan = FXPlan(
        name="Sample FX Plan",
        description="A sample FX plan for testing",
        effects_config={
            "voice_enhancement": {"enabled": True},
            "background_music": {"enabled": False}
        },
        priority=1,
        scene_id=sample_scene.id,
        project_id=sample_project.id,
        status="pending"
    )
    db_session.add(fx_plan)
    db_session.commit()
    db_session.refresh(fx_plan)
    return fx_plan


@pytest.fixture
def sample_render(db_session, sample_scene, sample_project):
    """Create sample render"""
    render = Render(
        name="Sample Render",
        description="A sample render for testing",
        render_type="stems",
        output_format="wav",
        sample_rate=44100,
        bit_depth=24,
        channels=2,
        scene_id=sample_scene.id,
        project_id=sample_project.id,
        status="completed",
        output_path="/path/to/render.wav",
        file_size=2048000,
        duration=120.0
    )
    db_session.add(render)
    db_session.commit()
    db_session.refresh(render)
    return render
