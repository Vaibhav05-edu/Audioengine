"""
Screenplay parsing API endpoints
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field

from ....database import get_db
from ....models import Project, User
from ....parsers.screenplay import ScreenplayParser, ScenePersistenceManager
from ....schemas import Scene as SceneSchema
from ...dependencies import get_current_active_user

router = APIRouter()


class ScreenplayParseRequest(BaseModel):
    """Request model for screenplay parsing"""
    screenplay_text: str = Field(..., min_length=1, description="Raw screenplay text to parse")
    project_id: int = Field(..., description="Project ID to associate scenes with")
    auto_persist: bool = Field(default=True, description="Whether to automatically persist scenes to database")


class ScreenplayParseResponse(BaseModel):
    """Response model for screenplay parsing"""
    success: bool
    message: str
    scenes_parsed: int
    scenes_persisted: int
    scenes: List[dict]
    errors: Optional[List[str]] = None


class ScreenplayUploadRequest(BaseModel):
    """Request model for screenplay file upload"""
    project_id: int = Field(..., description="Project ID to associate scenes with")
    auto_persist: bool = Field(default=True, description="Whether to automatically persist scenes to database")


class ScreenplayUploadResponse(BaseModel):
    """Response model for screenplay file upload"""
    success: bool
    message: str
    filename: str
    file_size: int
    scenes_parsed: int
    scenes_persisted: int
    scenes: List[dict]
    errors: Optional[List[str]] = None


@router.post("/parse", response_model=ScreenplayParseResponse)
def parse_screenplay(
    request: ScreenplayParseRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Parse screenplay text and extract scenes
    
    This endpoint parses raw screenplay text and extracts scene headings, dialogue,
    voice-over, and other elements. It can optionally persist the parsed scenes
    to the database.
    
    **Screenplay Format Support:**
    - Scene headings: INT/EXT. LOCATION - TIME OF DAY
    - Character names: ALL CAPS
    - Dialogue: Text following character names
    - Voice-over: Character names with (V.O.) or (VOICE OVER)
    - Parentheticals: (action) or (emotion)
    - Transitions: FADE IN, FADE OUT, CUT TO, etc.
    
    **Parsing Features:**
    - Automatic scene detection and numbering
    - Dialogue and voice-over separation
    - Parenthetical extraction
    - Timeline JSON generation
    - Scene metadata extraction
    
    Args:
        request: Screenplay parse request with text and project ID
        db: Database session
        current_user: Current authenticated user
    
    Returns:
        Parse response with scene data and statistics
    
    Raises:
        HTTPException: 404 if project not found, 400 if parsing fails
    """
    # Verify project exists
    project = db.query(Project).filter(Project.id == request.project_id).first()
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )
    
    try:
        # Parse screenplay
        parser = ScreenplayParser()
        parsed_scenes = parser.parse(request.screenplay_text)
        
        scenes_data = []
        scenes_persisted = 0
        
        if request.auto_persist and parsed_scenes:
            # Persist scenes to database
            persistence_manager = ScenePersistenceManager(db)
            persisted_scenes = persistence_manager.persist_scenes(parsed_scenes, request.project_id)
            scenes_persisted = len(persisted_scenes)
            scenes_data = persisted_scenes
        else:
            # Return parsed scene data without persisting
            scenes_data = [
                {
                    "scene_number": scene.scene_number,
                    "name": scene.name,
                    "description": scene.description,
                    "location": scene.heading.location,
                    "time_of_day": scene.heading.time_of_day,
                    "scene_type": scene.heading.scene_type.value,
                    "dialogue_count": len(scene.dialogue),
                    "voice_over_count": len(scene.voice_over),
                    "dialogue": scene.dialogue,
                    "voice_over": scene.voice_over,
                    "action_text": scene.action_text,
                    "raw_text": scene.raw_text
                }
                for scene in parsed_scenes
            ]
        
        return ScreenplayParseResponse(
            success=True,
            message=f"Successfully parsed {len(parsed_scenes)} scenes",
            scenes_parsed=len(parsed_scenes),
            scenes_persisted=scenes_persisted,
            scenes=scenes_data
        )
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to parse screenplay: {str(e)}"
        )


@router.post("/upload", response_model=ScreenplayUploadResponse)
async def upload_screenplay(
    file: UploadFile = File(...),
    project_id: int = Depends(lambda: None),  # Will be set from form data
    auto_persist: bool = Depends(lambda: True),  # Will be set from form data
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Upload and parse screenplay file
    
    This endpoint accepts a screenplay file upload and parses it to extract scenes.
    Supported file formats include .txt, .fdx (Final Draft), and .pdf files.
    
    **Supported Formats:**
    - .txt: Plain text screenplay
    - .fdx: Final Draft XML format
    - .pdf: PDF screenplay (text extraction)
    
    **File Processing:**
    1. File validation and size checking
    2. Text extraction (for non-text formats)
    3. Screenplay parsing
    4. Optional database persistence
    
    Args:
        file: Uploaded screenplay file
        project_id: Project ID to associate scenes with
        auto_persist: Whether to automatically persist scenes to database
        db: Database session
        current_user: Current authenticated user
    
    Returns:
        Upload response with parsing results and statistics
    
    Raises:
        HTTPException: 404 if project not found, 400 if file processing fails
    """
    # Verify project exists
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )
    
    # Validate file
    if not file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No filename provided"
        )
    
    # Check file size (limit to 10MB)
    file_size = 0
    content = await file.read()
    file_size = len(content)
    
    if file_size > 10 * 1024 * 1024:  # 10MB
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File size exceeds 10MB limit"
        )
    
    # Check file extension
    file_extension = file.filename.lower().split('.')[-1]
    if file_extension not in ['txt', 'fdx', 'pdf']:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unsupported file format. Supported formats: .txt, .fdx, .pdf"
        )
    
    try:
        # Extract text from file
        screenplay_text = _extract_text_from_file(content, file_extension)
        
        if not screenplay_text.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No text content found in file"
            )
        
        # Parse screenplay
        parser = ScreenplayParser()
        parsed_scenes = parser.parse(screenplay_text)
        
        scenes_data = []
        scenes_persisted = 0
        
        if auto_persist and parsed_scenes:
            # Persist scenes to database
            persistence_manager = ScenePersistenceManager(db)
            persisted_scenes = persistence_manager.persist_scenes(parsed_scenes, project_id)
            scenes_persisted = len(persisted_scenes)
            scenes_data = persisted_scenes
        else:
            # Return parsed scene data without persisting
            scenes_data = [
                {
                    "scene_number": scene.scene_number,
                    "name": scene.name,
                    "description": scene.description,
                    "location": scene.heading.location,
                    "time_of_day": scene.heading.time_of_day,
                    "scene_type": scene.heading.scene_type.value,
                    "dialogue_count": len(scene.dialogue),
                    "voice_over_count": len(scene.voice_over),
                    "dialogue": scene.dialogue,
                    "voice_over": scene.voice_over,
                    "action_text": scene.action_text,
                    "raw_text": scene.raw_text
                }
                for scene in parsed_scenes
            ]
        
        return ScreenplayUploadResponse(
            success=True,
            message=f"Successfully uploaded and parsed {file.filename}",
            filename=file.filename,
            file_size=file_size,
            scenes_parsed=len(parsed_scenes),
            scenes_persisted=scenes_persisted,
            scenes=scenes_data
        )
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to process file: {str(e)}"
        )


@router.get("/scenes/{project_id}", response_model=List[SceneSchema])
def get_project_scenes(
    project_id: int,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Get all scenes for a project
    
    This endpoint retrieves all scenes associated with a project, including
    their timeline JSON and metadata.
    
    Args:
        project_id: Project ID
        skip: Number of scenes to skip
        limit: Maximum number of scenes to return
        db: Database session
        current_user: Current authenticated user
    
    Returns:
        List of scenes with timeline data
    
    Raises:
        HTTPException: 404 if project not found
    """
    # Verify project exists
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )
    
    # Get scenes
    from ....models import Scene
    scenes = db.query(Scene).filter(
        Scene.project_id == project_id
    ).offset(skip).limit(limit).all()
    
    return scenes


@router.get("/scenes/{project_id}/timeline")
def get_project_timeline(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Get complete timeline for a project
    
    This endpoint retrieves the complete timeline JSON for all scenes in a project,
    providing a unified view of the entire screenplay structure.
    
    Args:
        project_id: Project ID
        db: Database session
        current_user: Current authenticated user
    
    Returns:
        Complete timeline JSON with all scenes
    
    Raises:
        HTTPException: 404 if project not found
    """
    # Verify project exists
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )
    
    # Get all scenes
    from ....models import Scene
    scenes = db.query(Scene).filter(
        Scene.project_id == project_id
    ).order_by(Scene.scene_number).all()
    
    # Build complete timeline
    complete_timeline = {
        "version": "1.0",
        "project_id": project_id,
        "project_name": project.name,
        "total_scenes": len(scenes),
        "scenes": []
    }
    
    for scene in scenes:
        scene_timeline = {
            "scene_id": scene.id,
            "scene_number": scene.scene_number,
            "name": scene.name,
            "location": scene.location,
            "time_of_day": scene.time_of_day,
            "timeline_json": scene.timeline_json
        }
        complete_timeline["scenes"].append(scene_timeline)
    
    return complete_timeline


def _extract_text_from_file(content: bytes, file_extension: str) -> str:
    """
    Extract text from uploaded file based on file extension
    
    Args:
        content: File content as bytes
        file_extension: File extension (txt, fdx, pdf)
        
    Returns:
        Extracted text content
    """
    if file_extension == 'txt':
        return content.decode('utf-8', errors='ignore')
    
    elif file_extension == 'fdx':
        # For Final Draft XML files, extract text content
        # This is a simplified implementation
        import xml.etree.ElementTree as ET
        try:
            root = ET.fromstring(content.decode('utf-8', errors='ignore'))
            # Extract text from Final Draft XML structure
            text_parts = []
            for elem in root.iter():
                if elem.text and elem.text.strip():
                    text_parts.append(elem.text.strip())
            return '\n'.join(text_parts)
        except ET.ParseError:
            # Fallback to raw text extraction
            return content.decode('utf-8', errors='ignore')
    
    elif file_extension == 'pdf':
        # For PDF files, extract text using PyPDF2 or similar
        # This is a placeholder implementation
        try:
            import PyPDF2
            import io
            pdf_reader = PyPDF2.PdfReader(io.BytesIO(content))
            text_parts = []
            for page in pdf_reader.pages:
                text_parts.append(page.extract_text())
            return '\n'.join(text_parts)
        except ImportError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="PDF processing not available. Please install PyPDF2."
            )
        except Exception:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to extract text from PDF file"
            )
    
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file format: {file_extension}"
        )
