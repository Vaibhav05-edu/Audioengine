"""
Tests for SFX API endpoints
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch, AsyncMock
from sqlalchemy.orm import Session

from backend.main import app
from backend.models import Scene, Asset, Project

client = TestClient(app)


def test_generate_sfx_sync(sample_scene, db_session):
    """Test synchronous SFX generation"""
    request_data = {
        "prompt": "Rain falling on leaves",
        "duration": 10.0,
        "seed": 12345,
        "loopable": False,
        "crossfade_duration": 0.5,
        "scene_id": sample_scene.id,
        "asset_name": "Test SFX",
        "async_processing": False
    }
    
    with patch('backend.api.v1.endpoints.sfx.ElevenLabsSFXClient') as mock_client:
        # Mock SFX client
        mock_result = Mock()
        mock_result.success = True
        mock_result.duration = 10.0
        mock_result.tiles_generated = 1
        mock_result.generation_time = 2.5
        mock_result.sample_rate = 48000
        mock_result.bit_depth = 24
        mock_result.audio_data = b"fake audio data"
        mock_result.seed_used = 12345
        
        mock_client_instance = mock_client.return_value
        mock_client_instance.generate_sfx.return_value = mock_result
        
        # Mock asyncio.run
        with patch('asyncio.run') as mock_asyncio_run:
            mock_asyncio_run.return_value = mock_result
            
            response = client.post("/api/v1/sfx/generate", json=request_data)
            assert response.status_code == 200
            
            data = response.json()
            assert data["success"] is True
            assert "SFX generated successfully" in data["message"]
            assert "result" in data
            assert data["result"]["duration"] == 10.0
            assert data["result"]["tiles_generated"] == 1


def test_generate_sfx_async(sample_scene, db_session):
    """Test asynchronous SFX generation"""
    request_data = {
        "prompt": "Rain falling on leaves",
        "duration": 10.0,
        "seed": 12345,
        "loopable": False,
        "crossfade_duration": 0.5,
        "scene_id": sample_scene.id,
        "asset_name": "Test SFX",
        "async_processing": True
    }
    
    with patch('backend.api.v1.endpoints.sfx.generate_sfx_task') as mock_task:
        # Mock Celery task
        mock_task.delay.return_value.id = "test-task-id"
        
        response = client.post("/api/v1/sfx/generate", json=request_data)
        assert response.status_code == 200
        
        data = response.json()
        assert data["success"] is True
        assert data["task_id"] == "test-task-id"
        assert data["result"] is None


def test_generate_sfx_loopable(sample_scene, db_session):
    """Test SFX generation with loopable option"""
    request_data = {
        "prompt": "Forest ambience",
        "duration": 30.0,
        "seed": 54321,
        "loopable": True,
        "crossfade_duration": 1.0,
        "scene_id": sample_scene.id,
        "asset_name": "Loopable Ambience",
        "async_processing": False
    }
    
    with patch('backend.api.v1.endpoints.sfx.ElevenLabsSFXClient') as mock_client:
        # Mock SFX client
        mock_result = Mock()
        mock_result.success = True
        mock_result.duration = 30.0
        mock_result.tiles_generated = 2
        mock_result.generation_time = 5.0
        mock_result.sample_rate = 48000
        mock_result.bit_depth = 24
        mock_result.audio_data = b"fake audio data"
        mock_result.seed_used = 54321
        
        mock_client_instance = mock_client.return_value
        mock_client_instance.generate_sfx.return_value = mock_result
        
        # Mock asyncio.run
        with patch('asyncio.run') as mock_asyncio_run:
            mock_asyncio_run.return_value = mock_result
            
            response = client.post("/api/v1/sfx/generate", json=request_data)
            assert response.status_code == 200
            
            data = response.json()
            assert data["success"] is True
            assert "SFX generated successfully" in data["message"]
            assert data["result"]["tiles_generated"] == 2


def test_generate_sfx_invalid_scene(db_session):
    """Test SFX generation with invalid scene ID"""
    request_data = {
        "prompt": "Test prompt",
        "duration": 10.0,
        "scene_id": 99999,  # Non-existent scene
        "async_processing": False
    }
    
    response = client.post("/api/v1/sfx/generate", json=request_data)
    assert response.status_code == 404
    assert "Scene not found" in response.json()["detail"]


def test_generate_sfx_duration_validation():
    """Test SFX generation with invalid duration"""
    request_data = {
        "prompt": "Test prompt",
        "duration": 0.5,  # Too short
        "async_processing": False
    }
    
    response = client.post("/api/v1/sfx/generate", json=request_data)
    assert response.status_code == 422  # Validation error


def test_generate_sfx_prompt_validation():
    """Test SFX generation with invalid prompt"""
    request_data = {
        "prompt": "",  # Empty prompt
        "duration": 10.0,
        "async_processing": False
    }
    
    response = client.post("/api/v1/sfx/generate", json=request_data)
    assert response.status_code == 422  # Validation error


def test_generate_ambience_sync(sample_scene, db_session):
    """Test synchronous ambience generation"""
    request_data = {
        "prompt": "Forest ambience with birds",
        "duration": 60.0,
        "seed": 98765,
        "crossfade_duration": 2.0,
        "scene_id": sample_scene.id,
        "asset_name": "Forest Ambience",
        "async_processing": False
    }
    
    with patch('backend.api.v1.endpoints.sfx.ElevenLabsSFXClient') as mock_client:
        # Mock SFX client
        mock_result = Mock()
        mock_result.success = True
        mock_result.duration = 60.0
        mock_result.tiles_generated = 3
        mock_result.generation_time = 8.0
        mock_result.sample_rate = 48000
        mock_result.bit_depth = 24
        mock_result.audio_data = b"fake audio data"
        mock_result.seed_used = 98765
        
        mock_client_instance = mock_client.return_value
        mock_client_instance.generate_sfx.return_value = mock_result
        
        # Mock asyncio.run
        with patch('asyncio.run') as mock_asyncio_run:
            mock_asyncio_run.return_value = mock_result
            
            response = client.post("/api/v1/sfx/generate-ambience", json=request_data)
            assert response.status_code == 200
            
            data = response.json()
            assert data["success"] is True
            assert "Ambience generated successfully" in data["message"]
            assert data["result"]["tiles_generated"] == 3
            assert data["result"]["loopable"] is True


def test_generate_ambience_async(sample_scene, db_session):
    """Test asynchronous ambience generation"""
    request_data = {
        "prompt": "Ocean waves",
        "duration": 120.0,
        "seed": 11111,
        "crossfade_duration": 1.5,
        "scene_id": sample_scene.id,
        "asset_name": "Ocean Waves",
        "async_processing": True
    }
    
    with patch('backend.api.v1.endpoints.sfx.generate_ambience_task') as mock_task:
        # Mock Celery task
        mock_task.delay.return_value.id = "test-ambience-task-id"
        
        response = client.post("/api/v1/sfx/generate-ambience", json=request_data)
        assert response.status_code == 200
        
        data = response.json()
        assert data["success"] is True
        assert data["task_id"] == "test-ambience-task-id"
        assert data["result"] is None


def test_generate_ambience_invalid_scene(db_session):
    """Test ambience generation with invalid scene ID"""
    request_data = {
        "prompt": "Test ambience",
        "duration": 30.0,
        "scene_id": 99999,  # Non-existent scene
        "async_processing": False
    }
    
    response = client.post("/api/v1/sfx/generate-ambience", json=request_data)
    assert response.status_code == 404
    assert "Scene not found" in response.json()["detail"]


def test_get_sfx_status():
    """Test getting SFX generation status"""
    with patch('backend.api.v1.endpoints.sfx.celery_app') as mock_celery:
        # Mock Celery task result
        mock_task = Mock()
        mock_task.state = 'SUCCESS'
        mock_task.result = {"success": True, "message": "SFX generated"}
        mock_celery.AsyncResult.return_value = mock_task
        
        response = client.get("/api/v1/sfx/status/test-task-id")
        assert response.status_code == 200
        
        data = response.json()
        assert data["task_id"] == "test-task-id"
        assert data["status"] == "SUCCESS"
        assert data["result"]["success"] is True


def test_get_sfx_status_pending():
    """Test getting SFX generation status when pending"""
    with patch('backend.api.v1.endpoints.sfx.celery_app') as mock_celery:
        # Mock Celery task result
        mock_task = Mock()
        mock_task.state = 'PENDING'
        mock_celery.AsyncResult.return_value = mock_task
        
        response = client.get("/api/v1/sfx/status/test-task-id")
        assert response.status_code == 200
        
        data = response.json()
        assert data["task_id"] == "test-task-id"
        assert data["status"] == "PENDING"
        assert "progress" in data


def test_get_sfx_status_progress():
    """Test getting SFX generation status when in progress"""
    with patch('backend.api.v1.endpoints.sfx.celery_app') as mock_celery:
        # Mock Celery task result
        mock_task = Mock()
        mock_task.state = 'PROGRESS'
        mock_task.info = {"current": 75, "total": 100, "status": "Generating tiles..."}
        mock_celery.AsyncResult.return_value = mock_task
        
        response = client.get("/api/v1/sfx/status/test-task-id")
        assert response.status_code == 200
        
        data = response.json()
        assert data["task_id"] == "test-task-id"
        assert data["status"] == "PROGRESS"
        assert data["progress"]["current"] == 75
        assert data["progress"]["total"] == 100


def test_get_sfx_status_failure():
    """Test getting SFX generation status when failed"""
    with patch('backend.api.v1.endpoints.sfx.celery_app') as mock_celery:
        # Mock Celery task result
        mock_task = Mock()
        mock_task.state = 'FAILURE'
        mock_task.info = "SFX generation failed: API error"
        mock_celery.AsyncResult.return_value = mock_task
        
        response = client.get("/api/v1/sfx/status/test-task-id")
        assert response.status_code == 200
        
        data = response.json()
        assert data["task_id"] == "test-task-id"
        assert data["status"] == "FAILURE"
        assert "SFX generation failed" in data["error"]


def test_get_sfx_cache_info():
    """Test getting SFX cache information"""
    with patch('backend.api.v1.endpoints.sfx.ElevenLabsSFXClient') as mock_client:
        # Mock SFX client
        mock_client_instance = mock_client.return_value
        mock_client_instance.get_cache_info.return_value = {
            "cache_dir": "/tmp/cache",
            "total_files": 5,
            "total_size_bytes": 1024000,
            "total_size_mb": 1.0
        }
        
        response = client.get("/api/v1/sfx/cache/info")
        assert response.status_code == 200
        
        data = response.json()
        assert data["cache_dir"] == "/tmp/cache"
        assert data["total_files"] == 5
        assert data["total_size_bytes"] == 1024000
        assert data["total_size_mb"] == 1.0


def test_clear_sfx_cache():
    """Test clearing SFX cache"""
    with patch('backend.api.v1.endpoints.sfx.ElevenLabsSFXClient') as mock_client:
        # Mock SFX client
        mock_client_instance = mock_client.return_value
        mock_client_instance.clear_cache.return_value = 3
        
        response = client.delete("/api/v1/sfx/cache?pattern=test*")
        assert response.status_code == 200
        
        data = response.json()
        assert data["success"] is True
        assert "Cleared 3 cached SFX results" in data["message"]


def test_clear_sfx_cache_async():
    """Test clearing SFX cache asynchronously"""
    with patch('backend.api.v1.endpoints.sfx.clear_sfx_cache_task') as mock_task:
        # Mock Celery task
        mock_task.delay.return_value.id = "test-cache-task-id"
        
        response = client.delete("/api/v1/sfx/cache?pattern=test*")
        assert response.status_code == 200
        
        data = response.json()
        assert data["success"] is True
        assert "Started clearing SFX cache" in data["message"]


def test_get_generated_assets(sample_scene, db_session):
    """Test getting generated assets for a scene"""
    # Create a generated asset
    generated_asset = Asset(
        name="Generated SFX",
        description="Test generated SFX",
        asset_type="sfx",
        file_path="/path/to/generated.wav",
        original_filename="generated.wav",
        file_size=1024000,
        duration=10.0,
        format="wav",
        sample_rate=48000,
        channels=1,
        bit_rate=48000 * 24,
        scene_id=sample_scene.id,
        project_id=sample_scene.project_id,
        metadata={
            "generated": True,
            "prompt": "Rain falling",
            "seed": 12345,
            "loopable": False,
            "tiles_generated": 1,
            "generation_time": 2.5,
            "generated_at": "2024-01-01T00:00:00"
        }
    )
    
    db_session.add(generated_asset)
    db_session.commit()
    db_session.refresh(generated_asset)
    
    response = client.get(f"/api/v1/sfx/generated-assets/{sample_scene.id}")
    assert response.status_code == 200
    
    data = response.json()
    assert data["scene_id"] == sample_scene.id
    assert data["total_assets"] == 1
    assert len(data["assets"]) == 1
    
    asset = data["assets"][0]
    assert asset["id"] == generated_asset.id
    assert asset["name"] == "Generated SFX"
    assert asset["asset_type"] == "sfx"
    assert asset["generation_metadata"]["prompt"] == "Rain falling"
    assert asset["generation_metadata"]["seed"] == 12345


def test_get_generated_assets_filtered(sample_scene, db_session):
    """Test getting generated assets with type filter"""
    # Create generated assets of different types
    sfx_asset = Asset(
        name="Generated SFX",
        asset_type="sfx",
        file_path="/path/to/sfx.wav",
        original_filename="sfx.wav",
        file_size=1024000,
        duration=10.0,
        format="wav",
        sample_rate=48000,
        channels=1,
        bit_rate=48000 * 24,
        scene_id=sample_scene.id,
        project_id=sample_scene.project_id,
        metadata={"generated": True, "prompt": "SFX prompt"}
    )
    
    ambience_asset = Asset(
        name="Generated Ambience",
        asset_type="ambience",
        file_path="/path/to/ambience.wav",
        original_filename="ambience.wav",
        file_size=2048000,
        duration=60.0,
        format="wav",
        sample_rate=48000,
        channels=1,
        bit_rate=48000 * 24,
        scene_id=sample_scene.id,
        project_id=sample_scene.project_id,
        metadata={"generated": True, "prompt": "Ambience prompt"}
    )
    
    db_session.add_all([sfx_asset, ambience_asset])
    db_session.commit()
    
    # Test filtering by SFX type
    response = client.get(f"/api/v1/sfx/generated-assets/{sample_scene.id}?asset_type=sfx")
    assert response.status_code == 200
    
    data = response.json()
    assert data["total_assets"] == 1
    assert data["assets"][0]["asset_type"] == "sfx"
    
    # Test filtering by ambience type
    response = client.get(f"/api/v1/sfx/generated-assets/{sample_scene.id}?asset_type=ambience")
    assert response.status_code == 200
    
    data = response.json()
    assert data["total_assets"] == 1
    assert data["assets"][0]["asset_type"] == "ambience"


def test_get_generated_assets_invalid_scene(db_session):
    """Test getting generated assets for invalid scene"""
    response = client.get("/api/v1/sfx/generated-assets/99999")
    assert response.status_code == 404
    assert "Scene not found" in response.json()["detail"]


def test_generate_sfx_processing_error(sample_scene, db_session):
    """Test SFX generation with processing error"""
    request_data = {
        "prompt": "Test prompt",
        "duration": 10.0,
        "scene_id": sample_scene.id,
        "async_processing": False
    }
    
    with patch('backend.api.v1.endpoints.sfx.ElevenLabsSFXClient') as mock_client:
        # Mock SFX client to raise exception
        mock_client_instance = mock_client.return_value
        mock_client_instance.generate_sfx.side_effect = Exception("API error")
        
        # Mock asyncio.run
        with patch('asyncio.run') as mock_asyncio_run:
            mock_asyncio_run.side_effect = Exception("API error")
            
            response = client.post("/api/v1/sfx/generate", json=request_data)
            assert response.status_code == 400
            assert "SFX generation failed" in response.json()["detail"]


def test_generate_sfx_without_scene():
    """Test SFX generation without scene association"""
    request_data = {
        "prompt": "Test prompt",
        "duration": 10.0,
        "async_processing": False
    }
    
    with patch('backend.api.v1.endpoints.sfx.ElevenLabsSFXClient') as mock_client:
        # Mock SFX client
        mock_result = Mock()
        mock_result.success = True
        mock_result.duration = 10.0
        mock_result.tiles_generated = 1
        mock_result.generation_time = 2.5
        mock_result.sample_rate = 48000
        mock_result.bit_depth = 24
        mock_result.audio_data = b"fake audio data"
        mock_result.seed_used = None
        
        mock_client_instance = mock_client.return_value
        mock_client_instance.generate_sfx.return_value = mock_result
        
        # Mock asyncio.run
        with patch('asyncio.run') as mock_asyncio_run:
            mock_asyncio_run.return_value = mock_result
            
            response = client.post("/api/v1/sfx/generate", json=request_data)
            assert response.status_code == 200
            
            data = response.json()
            assert data["success"] is True
            assert "SFX generated successfully" in data["message"]
