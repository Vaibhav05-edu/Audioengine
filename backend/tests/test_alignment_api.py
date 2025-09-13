"""
Tests for alignment API endpoints
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch
from sqlalchemy.orm import Session

from backend.main import app
from backend.models import Scene, Asset, Project

client = TestClient(app)


def test_align_vo_sync(sample_scene, sample_asset, db_session):
    """Test synchronous VO alignment"""
    request_data = {
        "scene_id": sample_scene.id,
        "asset_id": sample_asset.id,
        "language": "en",
        "force_reprocess": False,
        "async_processing": False
    }
    
    with patch('backend.api.v1.endpoints.alignment.WhisperXAlignmentService') as mock_service:
        # Mock alignment service
        mock_alignment_result = Mock()
        mock_alignment_result.scene_id = sample_scene.id
        mock_alignment_result.asset_id = sample_asset.id
        mock_alignment_result.language = "en"
        mock_alignment_result.total_duration = 10.0
        mock_alignment_result.processing_time = 2.5
        mock_alignment_result.model_used = "whisperx-large-v2"
        mock_alignment_result.created_at = "2024-01-01T00:00:00"
        
        mock_summary = {
            "scene_id": sample_scene.id,
            "asset_id": sample_asset.id,
            "language": "en",
            "total_segments": 5,
            "total_words": 25,
            "total_duration": 10.0,
            "average_confidence": 0.85,
            "processing_time": 2.5,
            "model_used": "whisperx-large-v2",
            "created_at": "2024-01-01T00:00:00"
        }
        
        mock_service_instance = mock_service.return_value
        mock_service_instance.align_audio.return_value = mock_alignment_result
        mock_service_instance.get_alignment_summary.return_value = mock_summary
        
        response = client.post("/api/v1/alignment/align_vo", json=request_data)
        assert response.status_code == 200
        
        data = response.json()
        assert data["success"] is True
        assert data["scene_id"] == sample_scene.id
        assert data["asset_id"] == sample_asset.id
        assert data["task_id"] is None
        assert "results" in data


def test_align_vo_async(sample_scene, sample_asset, db_session):
    """Test asynchronous VO alignment"""
    request_data = {
        "scene_id": sample_scene.id,
        "asset_id": sample_asset.id,
        "language": "en",
        "force_reprocess": False,
        "async_processing": True
    }
    
    with patch('backend.api.v1.endpoints.alignment.align_vo_asset_task') as mock_task:
        # Mock Celery task
        mock_task.delay.return_value.id = "test-task-id"
        
        response = client.post("/api/v1/alignment/align_vo", json=request_data)
        assert response.status_code == 200
        
        data = response.json()
        assert data["success"] is True
        assert data["scene_id"] == sample_scene.id
        assert data["asset_id"] == sample_asset.id
        assert data["task_id"] == "test-task-id"
        assert data["results"] is None


def test_align_vo_scene_async(sample_scene, db_session):
    """Test asynchronous scene VO alignment"""
    request_data = {
        "scene_id": sample_scene.id,
        "language": "en",
        "force_reprocess": False,
        "async_processing": True
    }
    
    with patch('backend.api.v1.endpoints.alignment.align_scene_vo_task') as mock_task:
        # Mock Celery task
        mock_task.delay.return_value.id = "test-scene-task-id"
        
        response = client.post("/api/v1/alignment/align_vo", json=request_data)
        assert response.status_code == 200
        
        data = response.json()
        assert data["success"] is True
        assert data["scene_id"] == sample_scene.id
        assert data["asset_id"] is None
        assert data["task_id"] == "test-scene-task-id"


def test_align_vo_invalid_scene(db_session):
    """Test VO alignment with invalid scene ID"""
    request_data = {
        "scene_id": 99999,
        "language": "en",
        "force_reprocess": False,
        "async_processing": False
    }
    
    response = client.post("/api/v1/alignment/align_vo", json=request_data)
    assert response.status_code == 404
    assert "Scene not found" in response.json()["detail"]


def test_align_vo_invalid_asset(sample_scene, db_session):
    """Test VO alignment with invalid asset ID"""
    request_data = {
        "scene_id": sample_scene.id,
        "asset_id": 99999,
        "language": "en",
        "force_reprocess": False,
        "async_processing": False
    }
    
    response = client.post("/api/v1/alignment/align_vo", json=request_data)
    assert response.status_code == 404
    assert "Asset not found" in response.json()["detail"]


def test_align_vo_asset_wrong_scene(sample_scene, sample_asset, db_session):
    """Test VO alignment with asset from different scene"""
    # Create another scene
    other_scene = Scene(
        name="Other Scene",
        description="Another scene",
        project_id=sample_scene.project_id
    )
    db_session.add(other_scene)
    db_session.commit()
    db_session.refresh(other_scene)
    
    request_data = {
        "scene_id": other_scene.id,
        "asset_id": sample_asset.id,
        "language": "en",
        "force_reprocess": False,
        "async_processing": False
    }
    
    response = client.post("/api/v1/alignment/align_vo", json=request_data)
    assert response.status_code == 400
    assert "Asset does not belong to the specified scene" in response.json()["detail"]


def test_get_alignment_status():
    """Test getting alignment task status"""
    with patch('backend.api.v1.endpoints.alignment.celery_app') as mock_celery:
        # Mock Celery task result
        mock_task = Mock()
        mock_task.state = 'SUCCESS'
        mock_task.result = {"success": True, "message": "Alignment completed"}
        mock_celery.AsyncResult.return_value = mock_task
        
        response = client.get("/api/v1/alignment/status/test-task-id")
        assert response.status_code == 200
        
        data = response.json()
        assert data["task_id"] == "test-task-id"
        assert data["status"] == "SUCCESS"
        assert data["result"]["success"] is True


def test_get_alignment_status_pending():
    """Test getting alignment task status when pending"""
    with patch('backend.api.v1.endpoints.alignment.celery_app') as mock_celery:
        # Mock Celery task result
        mock_task = Mock()
        mock_task.state = 'PENDING'
        mock_celery.AsyncResult.return_value = mock_task
        
        response = client.get("/api/v1/alignment/status/test-task-id")
        assert response.status_code == 200
        
        data = response.json()
        assert data["task_id"] == "test-task-id"
        assert data["status"] == "PENDING"
        assert "progress" in data


def test_get_alignment_status_progress():
    """Test getting alignment task status when in progress"""
    with patch('backend.api.v1.endpoints.alignment.celery_app') as mock_celery:
        # Mock Celery task result
        mock_task = Mock()
        mock_task.state = 'PROGRESS'
        mock_task.info = {"current": 50, "total": 100, "status": "Processing..."}
        mock_celery.AsyncResult.return_value = mock_task
        
        response = client.get("/api/v1/alignment/status/test-task-id")
        assert response.status_code == 200
        
        data = response.json()
        assert data["task_id"] == "test-task-id"
        assert data["status"] == "PROGRESS"
        assert data["progress"]["current"] == 50
        assert data["progress"]["total"] == 100


def test_get_alignment_status_failure():
    """Test getting alignment task status when failed"""
    with patch('backend.api.v1.endpoints.alignment.celery_app') as mock_celery:
        # Mock Celery task result
        mock_task = Mock()
        mock_task.state = 'FAILURE'
        mock_task.info = "Alignment failed: File not found"
        mock_celery.AsyncResult.return_value = mock_task
        
        response = client.get("/api/v1/alignment/status/test-task-id")
        assert response.status_code == 200
        
        data = response.json()
        assert data["task_id"] == "test-task-id"
        assert data["status"] == "FAILURE"
        assert "Alignment failed" in data["error"]


def test_get_alignment_results(sample_scene, sample_asset, db_session):
    """Test getting cached alignment results"""
    with patch('backend.api.v1.endpoints.alignment.WhisperXAlignmentService') as mock_service:
        # Mock alignment service and cached result
        mock_alignment_result = Mock()
        mock_alignment_result.scene_id = sample_scene.id
        mock_alignment_result.asset_id = sample_asset.id
        mock_alignment_result.language = "en"
        mock_alignment_result.segments = []
        mock_alignment_result.total_duration = 10.0
        mock_alignment_result.processing_time = 2.5
        mock_alignment_result.model_used = "whisperx-large-v2"
        mock_alignment_result.created_at = "2024-01-01T00:00:00"
        
        mock_service_instance = mock_service.return_value
        mock_service_instance.cache.get.return_value = mock_alignment_result
        
        response = client.get(f"/api/v1/alignment/results/{sample_scene.id}?asset_id={sample_asset.id}")
        assert response.status_code == 200
        
        data = response.json()
        assert len(data) == 1
        assert data[0]["scene_id"] == sample_scene.id
        assert data[0]["asset_id"] == sample_asset.id
        assert data[0]["language"] == "en"


def test_get_alignment_results_no_cache(sample_scene, sample_asset, db_session):
    """Test getting alignment results when no cache exists"""
    with patch('backend.api.v1.endpoints.alignment.WhisperXAlignmentService') as mock_service:
        # Mock alignment service with no cached result
        mock_service_instance = mock_service.return_value
        mock_service_instance.cache.get.return_value = None
        
        response = client.get(f"/api/v1/alignment/results/{sample_scene.id}?asset_id={sample_asset.id}")
        assert response.status_code == 200
        
        data = response.json()
        assert len(data) == 0


def test_get_alignment_results_invalid_scene(db_session):
    """Test getting alignment results for invalid scene"""
    response = client.get("/api/v1/alignment/results/99999")
    assert response.status_code == 404
    assert "Scene not found" in response.json()["detail"]


def test_clear_alignment_cache(sample_scene, db_session):
    """Test clearing alignment cache"""
    with patch('backend.api.v1.endpoints.alignment.WhisperXAlignmentService') as mock_service:
        # Mock alignment service
        mock_service_instance = mock_service.return_value
        
        response = client.delete(f"/api/v1/alignment/cache/{sample_scene.id}")
        assert response.status_code == 200
        
        data = response.json()
        assert data["success"] is True
        assert "Cleared cache" in data["message"]
        
        # Verify cache clear was called
        mock_service_instance.cache.clear.assert_called_once_with(sample_scene.id, None)


def test_clear_alignment_cache_specific_asset(sample_scene, sample_asset, db_session):
    """Test clearing alignment cache for specific asset"""
    with patch('backend.api.v1.endpoints.alignment.WhisperXAlignmentService') as mock_service:
        # Mock alignment service
        mock_service_instance = mock_service.return_value
        
        response = client.delete(f"/api/v1/alignment/cache/{sample_scene.id}?asset_id={sample_asset.id}")
        assert response.status_code == 200
        
        data = response.json()
        assert data["success"] is True
        assert "Cleared cache" in data["message"]
        
        # Verify cache clear was called with specific asset
        mock_service_instance.cache.clear.assert_called_once_with(sample_scene.id, sample_asset.id)


def test_clear_alignment_cache_invalid_scene(db_session):
    """Test clearing alignment cache for invalid scene"""
    response = client.delete("/api/v1/alignment/cache/99999")
    assert response.status_code == 404
    assert "Scene not found" in response.json()["detail"]


def test_clear_alignment_cache_invalid_asset(sample_scene, db_session):
    """Test clearing alignment cache for invalid asset"""
    response = client.delete(f"/api/v1/alignment/cache/{sample_scene.id}?asset_id=99999")
    assert response.status_code == 404
    assert "Asset not found" in response.json()["detail"]


def test_align_vo_processing_error(sample_scene, sample_asset, db_session):
    """Test VO alignment with processing error"""
    request_data = {
        "scene_id": sample_scene.id,
        "asset_id": sample_asset.id,
        "language": "en",
        "force_reprocess": False,
        "async_processing": False
    }
    
    with patch('backend.api.v1.endpoints.alignment.WhisperXAlignmentService') as mock_service:
        # Mock alignment service to raise exception
        mock_service_instance = mock_service.return_value
        mock_service_instance.align_audio.side_effect = Exception("Processing failed")
        
        response = client.post("/api/v1/alignment/align_vo", json=request_data)
        assert response.status_code == 400
        assert "Alignment failed" in response.json()["detail"]


def test_align_vo_scene_sync(sample_scene, db_session):
    """Test synchronous scene VO alignment"""
    request_data = {
        "scene_id": sample_scene.id,
        "language": "en",
        "force_reprocess": False,
        "async_processing": False
    }
    
    with patch('backend.api.v1.endpoints.alignment.WhisperXAlignmentService') as mock_service:
        # Mock alignment service
        mock_service_instance = mock_service.return_value
        mock_service_instance.align_scene_vo.return_value = {
            "scene_id": sample_scene.id,
            "scene_name": sample_scene.name,
            "alignments": [],
            "total_assets": 0,
            "successful_alignments": 0,
            "failed_alignments": 0
        }
        
        response = client.post("/api/v1/alignment/align_vo", json=request_data)
        assert response.status_code == 200
        
        data = response.json()
        assert data["success"] is True
        assert data["scene_id"] == sample_scene.id
        assert data["asset_id"] is None
        assert "results" in data
