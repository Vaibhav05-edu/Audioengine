"""
Tests for prompt generation API endpoints
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch
from sqlalchemy.orm import Session

from backend.main import app
from backend.models import Scene, FXPlan, Project

client = TestClient(app)


def test_generate_prompts_success(sample_scene, db_session):
    """Test successful prompt generation"""
    request_data = {
        "scene_id": sample_scene.id,
        "regenerate": False
    }
    
    with patch('backend.api.v1.endpoints.prompt_generation.PromptGenerator') as mock_generator:
        # Mock prompt generator
        mock_generator_instance = mock_generator.return_value
        mock_fx_plan_prompts = Mock()
        mock_fx_plan_prompts.ambience_prompts = [
            Mock(prompt="Forest ambience", prompt_type="ambience", confidence=0.8)
        ]
        mock_fx_plan_prompts.sfx_prompts = [
            Mock(prompt="Footstep sound", prompt_type="sfx", confidence=0.7)
        ]
        mock_fx_plan_prompts.generated_at = "2024-01-01T00:00:00"
        mock_fx_plan_prompts.__dict__ = {
            "scene_id": sample_scene.id,
            "scene_name": sample_scene.name,
            "generated_at": "2024-01-01T00:00:00",
            "ambience_prompts": [],
            "sfx_prompts": [],
            "manual_overrides": {},
            "analysis_summary": {}
        }
        
        mock_generator_instance.generate_fx_plan_prompts.return_value = mock_fx_plan_prompts
        
        response = client.post("/api/v1/prompts/generate", json=request_data)
        assert response.status_code == 200
        
        data = response.json()
        assert data["success"] is True
        assert data["scene_id"] == sample_scene.id
        assert "Generated" in data["message"]
        assert "fx_plan_id" in data


def test_generate_prompts_existing(sample_scene, db_session):
    """Test prompt generation when prompts already exist"""
    # Create existing FX plan
    existing_fx_plan = FXPlan(
        name="Existing FX Plan",
        description="Existing plan",
        effects_config={"prompts": {"ambience_prompts": [], "sfx_prompts": []}},
        status="pending",
        scene_id=sample_scene.id,
        project_id=sample_scene.project_id
    )
    db_session.add(existing_fx_plan)
    db_session.commit()
    db_session.refresh(existing_fx_plan)
    
    request_data = {
        "scene_id": sample_scene.id,
        "regenerate": False
    }
    
    response = client.post("/api/v1/prompts/generate", json=request_data)
    assert response.status_code == 200
    
    data = response.json()
    assert data["success"] is True
    assert "already exist" in data["message"]
    assert data["fx_plan_id"] == existing_fx_plan.id


def test_generate_prompts_regenerate(sample_scene, db_session):
    """Test prompt generation with regenerate flag"""
    # Create existing FX plan
    existing_fx_plan = FXPlan(
        name="Existing FX Plan",
        description="Existing plan",
        effects_config={"prompts": {"ambience_prompts": [], "sfx_prompts": []}},
        status="pending",
        scene_id=sample_scene.id,
        project_id=sample_scene.project_id
    )
    db_session.add(existing_fx_plan)
    db_session.commit()
    db_session.refresh(existing_fx_plan)
    
    request_data = {
        "scene_id": sample_scene.id,
        "regenerate": True
    }
    
    with patch('backend.api.v1.endpoints.prompt_generation.PromptGenerator') as mock_generator:
        # Mock prompt generator
        mock_generator_instance = mock_generator.return_value
        mock_fx_plan_prompts = Mock()
        mock_fx_plan_prompts.generated_at = "2024-01-01T00:00:00"
        mock_fx_plan_prompts.__dict__ = {
            "scene_id": sample_scene.id,
            "scene_name": sample_scene.name,
            "generated_at": "2024-01-01T00:00:00",
            "ambience_prompts": [],
            "sfx_prompts": [],
            "manual_overrides": {},
            "analysis_summary": {}
        }
        
        mock_generator_instance.generate_fx_plan_prompts.return_value = mock_fx_plan_prompts
        
        response = client.post("/api/v1/prompts/generate", json=request_data)
        assert response.status_code == 200
        
        data = response.json()
        assert data["success"] is True
        assert "Generated" in data["message"]


def test_generate_prompts_invalid_scene(db_session):
    """Test prompt generation with invalid scene ID"""
    request_data = {
        "scene_id": 99999,
        "regenerate": False
    }
    
    response = client.post("/api/v1/prompts/generate", json=request_data)
    assert response.status_code == 404
    assert "Scene not found" in response.json()["detail"]


def test_generate_prompts_processing_error(sample_scene, db_session):
    """Test prompt generation with processing error"""
    request_data = {
        "scene_id": sample_scene.id,
        "regenerate": False
    }
    
    with patch('backend.api.v1.endpoints.prompt_generation.PromptGenerator') as mock_generator:
        # Mock generator to raise exception
        mock_generator_instance = mock_generator.return_value
        mock_generator_instance.generate_fx_plan_prompts.side_effect = Exception("Processing failed")
        
        response = client.post("/api/v1/prompts/generate", json=request_data)
        assert response.status_code == 400
        assert "Prompt generation failed" in response.json()["detail"]


def test_get_scene_prompts_success(sample_scene, db_session):
    """Test getting scene prompts successfully"""
    # Create FX plan with prompts
    fx_plan = FXPlan(
        name="Test FX Plan",
        description="Test plan",
        effects_config={
            "prompts": {
                "scene_id": sample_scene.id,
                "scene_name": sample_scene.name,
                "generated_at": "2024-01-01T00:00:00",
                "ambience_prompts": [],
                "sfx_prompts": [],
                "manual_overrides": {},
                "analysis_summary": {
                    "scene_heading": "Test",
                    "location": "room",
                    "time_of_day": "day",
                    "mood": None,
                    "verbs": [],
                    "nouns": [],
                    "adjectives": [],
                    "action_words": [],
                    "sound_cues": [],
                    "environment_cues": []
                }
            }
        },
        status="pending",
        scene_id=sample_scene.id,
        project_id=sample_scene.project_id
    )
    db_session.add(fx_plan)
    db_session.commit()
    db_session.refresh(fx_plan)
    
    response = client.get(f"/api/v1/prompts/scene/{sample_scene.id}")
    assert response.status_code == 200
    
    data = response.json()
    assert data["scene_id"] == sample_scene.id
    assert data["scene_name"] == sample_scene.name
    assert data["fx_plan_id"] == fx_plan.id
    assert data["has_prompts"] is True
    assert "prompts" in data


def test_get_scene_prompts_no_prompts(sample_scene, db_session):
    """Test getting scene prompts when no prompts exist"""
    response = client.get(f"/api/v1/prompts/scene/{sample_scene.id}")
    assert response.status_code == 200
    
    data = response.json()
    assert data["scene_id"] == sample_scene.id
    assert data["scene_name"] == sample_scene.name
    assert data["fx_plan_id"] is None
    assert data["has_prompts"] is False
    assert data["prompts"] is None


def test_get_scene_prompts_invalid_scene(db_session):
    """Test getting scene prompts for invalid scene"""
    response = client.get("/api/v1/prompts/scene/99999")
    assert response.status_code == 404
    assert "Scene not found" in response.json()["detail"]


def test_override_prompt_success(sample_scene, db_session):
    """Test successful prompt override"""
    # Create FX plan with prompts
    fx_plan = FXPlan(
        name="Test FX Plan",
        description="Test plan",
        effects_config={
            "prompts": {
                "scene_id": sample_scene.id,
                "scene_name": sample_scene.name,
                "generated_at": "2024-01-01T00:00:00",
                "ambience_prompts": [
                    {
                        "prompt": "Forest ambience",
                        "prompt_type": "ambience",
                        "confidence": 0.8,
                        "source_elements": ["forest"],
                        "template_used": "location",
                        "manual_override": False,
                        "override_reason": None
                    }
                ],
                "sfx_prompts": [],
                "manual_overrides": {},
                "analysis_summary": {
                    "scene_heading": "Test",
                    "location": "room",
                    "time_of_day": "day",
                    "mood": None,
                    "verbs": [],
                    "nouns": [],
                    "adjectives": [],
                    "action_words": [],
                    "sound_cues": [],
                    "environment_cues": []
                }
            }
        },
        status="pending",
        scene_id=sample_scene.id,
        project_id=sample_scene.project_id
    )
    db_session.add(fx_plan)
    db_session.commit()
    db_session.refresh(fx_plan)
    
    request_data = {
        "prompt_id": "Forest ambience",
        "new_prompt": "Custom forest ambience with birds",
        "reason": "Added bird sounds"
    }
    
    with patch('backend.api.v1.endpoints.prompt_generation.PromptGenerator') as mock_generator:
        # Mock prompt generator
        mock_generator_instance = mock_generator.return_value
        mock_updated_prompts = Mock()
        mock_updated_prompts.generated_at = "2024-01-01T00:00:00"
        mock_updated_prompts.__dict__ = {
            "scene_id": sample_scene.id,
            "scene_name": sample_scene.name,
            "generated_at": "2024-01-01T00:00:00",
            "ambience_prompts": [],
            "sfx_prompts": [],
            "manual_overrides": {},
            "analysis_summary": {}
        }
        
        mock_generator_instance.apply_manual_override.return_value = mock_updated_prompts
        
        response = client.put(f"/api/v1/prompts/override?scene_id={sample_scene.id}", json=request_data)
        assert response.status_code == 200
        
        data = response.json()
        assert data["success"] is True
        assert data["prompt_id"] == "Forest ambience"
        assert data["new_prompt"] == "Custom forest ambience with birds"
        assert data["reason"] == "Added bird sounds"


def test_override_prompt_invalid_scene(db_session):
    """Test prompt override with invalid scene ID"""
    request_data = {
        "prompt_id": "Test prompt",
        "new_prompt": "New prompt",
        "reason": "Test reason"
    }
    
    response = client.put("/api/v1/prompts/override?scene_id=99999", json=request_data)
    assert response.status_code == 404
    assert "Scene not found" in response.json()["detail"]


def test_override_prompt_no_fx_plan(sample_scene, db_session):
    """Test prompt override when no FX plan exists"""
    request_data = {
        "prompt_id": "Test prompt",
        "new_prompt": "New prompt",
        "reason": "Test reason"
    }
    
    response = client.put(f"/api/v1/prompts/override?scene_id={sample_scene.id}", json=request_data)
    assert response.status_code == 404
    assert "FX plan not found" in response.json()["detail"]


def test_get_scene_analysis_success(sample_scene, db_session):
    """Test getting scene analysis successfully"""
    with patch('backend.api.v1.endpoints.prompt_generation.PromptGenerator') as mock_generator:
        # Mock prompt generator
        mock_generator_instance = mock_generator.return_value
        mock_analysis = Mock()
        mock_analysis.scene_heading = "Test Scene"
        mock_analysis.location = "room"
        mock_analysis.time_of_day = "day"
        mock_analysis.mood = None
        mock_analysis.verbs = ["walk"]
        mock_analysis.nouns = ["door"]
        mock_analysis.adjectives = []
        mock_analysis.action_words = ["walk"]
        mock_analysis.sound_cues = []
        mock_analysis.environment_cues = []
        
        mock_generator_instance.analyzer.analyze_scene.return_value = mock_analysis
        
        response = client.get(f"/api/v1/prompts/analysis/{sample_scene.id}")
        assert response.status_code == 200
        
        data = response.json()
        assert data["scene_heading"] == "Test Scene"
        assert data["location"] == "room"
        assert data["time_of_day"] == "day"


def test_get_scene_analysis_invalid_scene(db_session):
    """Test getting scene analysis for invalid scene"""
    response = client.get("/api/v1/prompts/analysis/99999")
    assert response.status_code == 404
    assert "Scene not found" in response.json()["detail"]


def test_get_scene_analysis_processing_error(sample_scene, db_session):
    """Test getting scene analysis with processing error"""
    with patch('backend.api.v1.endpoints.prompt_generation.PromptGenerator') as mock_generator:
        # Mock generator to raise exception
        mock_generator_instance = mock_generator.return_value
        mock_generator_instance.analyzer.analyze_scene.side_effect = Exception("Analysis failed")
        
        response = client.get(f"/api/v1/prompts/analysis/{sample_scene.id}")
        assert response.status_code == 400
        assert "Scene analysis failed" in response.json()["detail"]


def test_get_prompt_templates():
    """Test getting prompt templates"""
    response = client.get("/api/v1/prompts/templates")
    assert response.status_code == 200
    
    data = response.json()
    assert "ambience_templates" in data
    assert "sfx_templates" in data
    assert "surface_mappings" in data
    assert "object_mappings" in data
    
    # Check template structure
    assert "location" in data["ambience_templates"]
    assert "time" in data["ambience_templates"]
    assert "mood" in data["ambience_templates"]
    assert "action" in data["sfx_templates"]
    assert "environment" in data["sfx_templates"]
    assert "objects" in data["sfx_templates"]


def test_clear_scene_prompts_success(sample_scene, db_session):
    """Test clearing scene prompts successfully"""
    # Create FX plan with prompts
    fx_plan = FXPlan(
        name="Test FX Plan",
        description="Test plan",
        effects_config={
            "prompts": {
                "ambience_prompts": [],
                "sfx_prompts": []
            }
        },
        status="pending",
        scene_id=sample_scene.id,
        project_id=sample_scene.project_id
    )
    db_session.add(fx_plan)
    db_session.commit()
    db_session.refresh(fx_plan)
    
    response = client.delete(f"/api/v1/prompts/scene/{sample_scene.id}")
    assert response.status_code == 200
    
    data = response.json()
    assert data["success"] is True
    assert f"Cleared prompts for scene {sample_scene.id}" in data["message"]


def test_clear_scene_prompts_no_fx_plan(sample_scene, db_session):
    """Test clearing scene prompts when no FX plan exists"""
    response = client.delete(f"/api/v1/prompts/scene/{sample_scene.id}")
    assert response.status_code == 200
    
    data = response.json()
    assert data["success"] is True
    assert f"Cleared prompts for scene {sample_scene.id}" in data["message"]


def test_clear_scene_prompts_invalid_scene(db_session):
    """Test clearing scene prompts for invalid scene"""
    response = client.delete("/api/v1/prompts/scene/99999")
    assert response.status_code == 404
    assert "Scene not found" in response.json()["detail"]


def test_generate_prompts_with_screenplay_data(sample_scene, db_session):
    """Test prompt generation with screenplay data"""
    # Add screenplay data to scene
    sample_scene.screenplay_data = {
        "dialogue": [
            {"text": "Hello there!"},
            {"text": "How are you?"}
        ],
        "action": [
            {"text": "John walks across the room"},
            {"text": "The door creaks open"}
        ]
    }
    db_session.commit()
    
    request_data = {
        "scene_id": sample_scene.id,
        "regenerate": False
    }
    
    with patch('backend.api.v1.endpoints.prompt_generation.PromptGenerator') as mock_generator:
        # Mock prompt generator
        mock_generator_instance = mock_generator.return_value
        mock_fx_plan_prompts = Mock()
        mock_fx_plan_prompts.generated_at = "2024-01-01T00:00:00"
        mock_fx_plan_prompts.__dict__ = {
            "scene_id": sample_scene.id,
            "scene_name": sample_scene.name,
            "generated_at": "2024-01-01T00:00:00",
            "ambience_prompts": [],
            "sfx_prompts": [],
            "manual_overrides": {},
            "analysis_summary": {}
        }
        
        mock_generator_instance.generate_fx_plan_prompts.return_value = mock_fx_plan_prompts
        
        response = client.post("/api/v1/prompts/generate", json=request_data)
        assert response.status_code == 200
        
        data = response.json()
        assert data["success"] is True
        
        # Verify that the generator was called with screenplay data
        mock_generator_instance.generate_fx_plan_prompts.assert_called_once()
        call_args = mock_generator_instance.generate_fx_plan_prompts.call_args
        scene_text = call_args[0][1]  # Second argument is scene_text
        assert "Hello there!" in scene_text
        assert "John walks across the room" in scene_text
