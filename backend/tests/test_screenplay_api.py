"""
Tests for screenplay API endpoints
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from backend.main import app
from backend.models import Project, Scene

client = TestClient(app)


def test_parse_screenplay(sample_project, db_session):
    """Test screenplay parsing endpoint"""
    screenplay_text = """
INT. LIVING ROOM - DAY

John sits on the couch.

JOHN
Hello there.

MARY (V.O.)
I was thinking about him.

EXT. GARDEN - EVENING

Mary walks through the garden.

MARY
What a beautiful evening.
"""

    request_data = {
        "screenplay_text": screenplay_text,
        "project_id": sample_project.id,
        "auto_persist": True,
    }

    response = client.post("/api/v1/screenplay/parse", json=request_data)
    assert response.status_code == 200

    data = response.json()
    assert data["success"] is True
    assert data["scenes_parsed"] == 2
    assert data["scenes_persisted"] == 2
    assert len(data["scenes"]) == 2

    # Test first scene
    scene1 = data["scenes"][0]
    assert scene1["location"] == "LIVING ROOM"
    assert scene1["time_of_day"] == "DAY"
    assert scene1["dialogue_count"] == 1
    assert scene1["voice_over_count"] == 1

    # Test second scene
    scene2 = data["scenes"][1]
    assert scene2["location"] == "GARDEN"
    assert scene2["time_of_day"] == "EVENING"
    assert scene2["dialogue_count"] == 1
    assert scene2["voice_over_count"] == 0


def test_parse_screenplay_without_persistence(sample_project, db_session):
    """Test screenplay parsing without database persistence"""
    screenplay_text = """
INT. LIVING ROOM - DAY

JOHN
Hello there.
"""

    request_data = {
        "screenplay_text": screenplay_text,
        "project_id": sample_project.id,
        "auto_persist": False,
    }

    response = client.post("/api/v1/screenplay/parse", json=request_data)
    assert response.status_code == 200

    data = response.json()
    assert data["success"] is True
    assert data["scenes_parsed"] == 1
    assert data["scenes_persisted"] == 0
    assert len(data["scenes"]) == 1

    # Check that scene data is returned but not persisted
    scene = data["scenes"][0]
    assert scene["location"] == "LIVING ROOM"
    assert "dialogue" in scene
    assert "voice_over" in scene
    assert "raw_text" in scene


def test_parse_screenplay_invalid_project(db_session):
    """Test screenplay parsing with invalid project ID"""
    screenplay_text = """
INT. LIVING ROOM - DAY

JOHN
Hello there.
"""

    request_data = {
        "screenplay_text": screenplay_text,
        "project_id": 99999,  # Non-existent project
        "auto_persist": True,
    }

    response = client.post("/api/v1/screenplay/parse", json=request_data)
    assert response.status_code == 404
    assert "Project not found" in response.json()["detail"]


def test_parse_screenplay_empty_text(sample_project, db_session):
    """Test screenplay parsing with empty text"""
    request_data = {
        "screenplay_text": "",
        "project_id": sample_project.id,
        "auto_persist": True,
    }

    response = client.post("/api/v1/screenplay/parse", json=request_data)
    assert response.status_code == 422  # Validation error


def test_upload_screenplay_txt(sample_project, db_session):
    """Test screenplay file upload with TXT file"""
    screenplay_content = """
INT. LIVING ROOM - DAY

JOHN
Hello there.

MARY
Hi John.
"""

    files = {"file": ("test_script.txt", screenplay_content, "text/plain")}
    data = {"project_id": sample_project.id, "auto_persist": True}

    response = client.post("/api/v1/screenplay/upload", files=files, data=data)
    assert response.status_code == 200

    response_data = response.json()
    assert response_data["success"] is True
    assert response_data["filename"] == "test_script.txt"
    assert response_data["scenes_parsed"] == 1
    assert response_data["scenes_persisted"] == 1


def test_upload_screenplay_invalid_format(sample_project, db_session):
    """Test screenplay file upload with invalid file format"""
    files = {"file": ("test_script.doc", b"Some content", "application/msword")}
    data = {"project_id": sample_project.id, "auto_persist": True}

    response = client.post("/api/v1/screenplay/upload", files=files, data=data)
    assert response.status_code == 400
    assert "Unsupported file format" in response.json()["detail"]


def test_upload_screenplay_invalid_project(db_session):
    """Test screenplay file upload with invalid project ID"""
    files = {
        "file": (
            "test_script.txt",
            "INT. LIVING ROOM - DAY\nJOHN\nHello.",
            "text/plain",
        )
    }
    data = {"project_id": 99999, "auto_persist": True}  # Non-existent project

    response = client.post("/api/v1/screenplay/upload", files=files, data=data)
    assert response.status_code == 404
    assert "Project not found" in response.json()["detail"]


def test_get_project_scenes(sample_project, sample_scene, db_session):
    """Test getting scenes for a project"""
    response = client.get(f"/api/v1/screenplay/scenes/{sample_project.id}")
    assert response.status_code == 200

    scenes = response.json()
    assert len(scenes) == 1
    assert scenes[0]["id"] == sample_scene.id
    assert scenes[0]["name"] == sample_scene.name
    assert scenes[0]["project_id"] == sample_project.id


def test_get_project_scenes_invalid_project(db_session):
    """Test getting scenes for invalid project"""
    response = client.get("/api/v1/screenplay/scenes/99999")
    assert response.status_code == 404
    assert "Project not found" in response.json()["detail"]


def test_get_project_timeline(sample_project, sample_scene, db_session):
    """Test getting complete timeline for a project"""
    response = client.get(f"/api/v1/screenplay/scenes/{sample_project.id}/timeline")
    assert response.status_code == 200

    timeline = response.json()
    assert timeline["project_id"] == sample_project.id
    assert timeline["project_name"] == sample_project.name
    assert timeline["total_scenes"] == 1
    assert len(timeline["scenes"]) == 1

    scene_timeline = timeline["scenes"][0]
    assert scene_timeline["scene_id"] == sample_scene.id
    assert scene_timeline["scene_number"] == sample_scene.scene_number
    assert "timeline_json" in scene_timeline


def test_get_project_timeline_invalid_project(db_session):
    """Test getting timeline for invalid project"""
    response = client.get("/api/v1/screenplay/scenes/99999/timeline")
    assert response.status_code == 404
    assert "Project not found" in response.json()["detail"]


def test_parse_complex_screenplay(sample_project, db_session):
    """Test parsing a complex screenplay with multiple elements"""
    screenplay_text = """
FADE IN:

INT. COFFEE SHOP - MORNING

The coffee shop is bustling with morning commuters.

SARAH
(to herself)
I need to finish this report.

WAITER
Good morning! What can I get you?

SARAH
A large coffee, please.

SARAH (V.O.)
I remember this day clearly.

CUT TO:

EXT. STREET - CONTINUOUS

Sarah walks down the busy street.

SARAH
(whispering)
Today is the day.

FADE OUT.
"""

    request_data = {
        "screenplay_text": screenplay_text,
        "project_id": sample_project.id,
        "auto_persist": True,
    }

    response = client.post("/api/v1/screenplay/parse", json=request_data)
    assert response.status_code == 200

    data = response.json()
    assert data["success"] is True
    assert data["scenes_parsed"] == 2
    assert data["scenes_persisted"] == 2

    # Test first scene
    scene1 = data["scenes"][0]
    assert scene1["location"] == "COFFEE SHOP"
    assert scene1["time_of_day"] == "MORNING"
    assert scene1["dialogue_count"] == 3
    assert scene1["voice_over_count"] == 1

    # Test second scene
    scene2 = data["scenes"][1]
    assert scene2["location"] == "STREET"
    assert scene2["time_of_day"] == "CONTINUOUS"
    assert scene2["dialogue_count"] == 1
    assert scene2["voice_over_count"] == 0


def test_parse_screenplay_with_parentheticals(sample_project, db_session):
    """Test parsing screenplay with parentheticals"""
    screenplay_text = """
INT. LIVING ROOM - DAY

JOHN
(smiling)
Hello there.

MARY
(confused)
What did you say?

JOHN
(laughing)
I said hello!
"""

    request_data = {
        "screenplay_text": screenplay_text,
        "project_id": sample_project.id,
        "auto_persist": False,  # Don't persist to check raw data
    }

    response = client.post("/api/v1/screenplay/parse", json=request_data)
    assert response.status_code == 200

    data = response.json()
    assert data["success"] is True
    assert data["scenes_parsed"] == 1

    scene = data["scenes"][0]
    assert scene["dialogue_count"] == 3

    # Check dialogue data includes parentheticals
    dialogue = scene["dialogue"]
    assert dialogue[0]["parenthetical"] == "(smiling)"
    assert dialogue[1]["parenthetical"] == "(confused)"
    assert dialogue[2]["parenthetical"] == "(laughing)"


def test_parse_screenplay_voice_over_variations(sample_project, db_session):
    """Test parsing screenplay with different voice-over formats"""
    screenplay_text = """
INT. LIVING ROOM - DAY

JOHN (V.O.)
This is what I was thinking.

MARY (VOICE OVER)
I was remembering the past.

NARRATOR (VOICE-OVER)
The story continues.

JOHN
Speaking normally now.
"""

    request_data = {
        "screenplay_text": screenplay_text,
        "project_id": sample_project.id,
        "auto_persist": False,
    }

    response = client.post("/api/v1/screenplay/parse", json=request_data)
    assert response.status_code == 200

    data = response.json()
    assert data["success"] is True
    assert data["scenes_parsed"] == 1

    scene = data["scenes"][0]
    assert scene["dialogue_count"] == 1
    assert scene["voice_over_count"] == 3

    # Check voice-over data
    voice_over = scene["voice_over"]
    assert voice_over[0]["character"] == "JOHN (V.O.)"
    assert voice_over[1]["character"] == "MARY (VOICE OVER)"
    assert voice_over[2]["character"] == "NARRATOR (VOICE-OVER)"

    # Check dialogue data
    dialogue = scene["dialogue"]
    assert dialogue[0]["character"] == "JOHN"
    assert dialogue[0]["is_voice_over"] is False
