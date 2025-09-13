"""
Tests for workflow endpoints
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from backend.main import app
from backend.models import Scene, Project, Asset, FXPlan, Render

client = TestClient(app)


def test_ingest_asset(sample_scene, db_session):
    """Test asset ingestion endpoint"""
    request_data = {
        "scene_id": sample_scene.id,
        "asset_type": "dialogue",
        "file": "dGVzdCBhdWRpbyBkYXRh",  # Base64 encoded "test audio data"
        "name": "Test Dialogue",
        "description": "Test dialogue asset",
        "start_time": 0.0,
        "volume": 1.0,
        "pan": 0.0,
        "loop": False,
        "fade_in": 0.0,
        "fade_out": 0.0
    }
    
    response = client.post("/api/v1/workflow/ingest", json=request_data)
    assert response.status_code == 201
    
    data = response.json()
    assert data["scene_id"] == sample_scene.id
    assert data["name"] == "Test Dialogue"
    assert data["asset_type"] == "dialogue"
    assert "asset_id" in data


def test_plan_fx(sample_scene, db_session):
    """Test FX planning endpoint"""
    request_data = {
        "scene_id": sample_scene.id,
        "plan_name": "Test FX Plan",
        "description": "Test FX plan for scene",
        "effects_config": {
            "voice_enhancement": {"enabled": True},
            "background_music": {"enabled": False}
        },
        "priority": 1
    }
    
    response = client.post("/api/v1/workflow/plan_fx", json=request_data)
    assert response.status_code == 201
    
    data = response.json()
    assert data["scene_id"] == sample_scene.id
    assert data["name"] == "Test FX Plan"
    assert data["status"] == "pending"
    assert "fx_plan_id" in data


def test_gen_fx(sample_fx_plan, db_session):
    """Test FX generation endpoint"""
    request_data = {
        "fx_plan_id": sample_fx_plan.id,
        "force_regenerate": False
    }
    
    response = client.post("/api/v1/workflow/gen_fx", json=request_data)
    assert response.status_code == 200
    
    data = response.json()
    assert data["fx_plan_id"] == sample_fx_plan.id
    assert data["status"] in ["pending", "processing", "completed"]
    assert "progress" in data


def test_render_stems(sample_scene, db_session):
    """Test render stems endpoint"""
    request_data = {
        "scene_id": sample_scene.id,
        "render_name": "Test Render",
        "render_type": "stems",
        "output_format": "wav",
        "sample_rate": 44100,
        "bit_depth": 24,
        "channels": 2
    }
    
    response = client.post("/api/v1/workflow/render_stems", json=request_data)
    assert response.status_code == 201
    
    data = response.json()
    assert data["scene_id"] == sample_scene.id
    assert data["name"] == "Test Render"
    assert data["render_type"] == "stems"
    assert data["status"] in ["pending", "processing", "completed"]
    assert "render_id" in data


def test_download_render(sample_render, db_session):
    """Test download render endpoint"""
    request_data = {
        "render_id": sample_render.id
    }
    
    response = client.post("/api/v1/workflow/download", json=request_data)
    assert response.status_code == 200
    
    data = response.json()
    assert data["render_id"] == sample_render.id
    assert "download_url" in data
    assert "expires_at" in data


def test_ingest_asset_invalid_scene(db_session):
    """Test asset ingestion with invalid scene ID"""
    request_data = {
        "scene_id": 99999,  # Non-existent scene
        "asset_type": "dialogue",
        "file": "dGVzdCBhdWRpbyBkYXRh",
        "name": "Test Dialogue"
    }
    
    response = client.post("/api/v1/workflow/ingest", json=request_data)
    assert response.status_code == 404
    assert "Scene not found" in response.json()["detail"]


def test_plan_fx_invalid_scene(db_session):
    """Test FX planning with invalid scene ID"""
    request_data = {
        "scene_id": 99999,  # Non-existent scene
        "plan_name": "Test FX Plan"
    }
    
    response = client.post("/api/v1/workflow/plan_fx", json=request_data)
    assert response.status_code == 404
    assert "Scene not found" in response.json()["detail"]


def test_gen_fx_invalid_plan(db_session):
    """Test FX generation with invalid FX plan ID"""
    request_data = {
        "fx_plan_id": 99999,  # Non-existent FX plan
        "force_regenerate": False
    }
    
    response = client.post("/api/v1/workflow/gen_fx", json=request_data)
    assert response.status_code == 404
    assert "FX plan not found" in response.json()["detail"]


def test_render_stems_invalid_scene(db_session):
    """Test render stems with invalid scene ID"""
    request_data = {
        "scene_id": 99999,  # Non-existent scene
        "render_name": "Test Render",
        "render_type": "stems"
    }
    
    response = client.post("/api/v1/workflow/render_stems", json=request_data)
    assert response.status_code == 404
    assert "Scene not found" in response.json()["detail"]


def test_download_render_invalid_render(db_session):
    """Test download render with invalid render ID"""
    request_data = {
        "render_id": 99999  # Non-existent render
    }
    
    response = client.post("/api/v1/workflow/download", json=request_data)
    assert response.status_code == 404
    assert "Render not found" in response.json()["detail"]
