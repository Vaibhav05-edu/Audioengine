"""
Scenes API endpoints
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from ....database import get_db
from ....models import Scene, Project, User
from ....schemas import SceneCreate, SceneUpdate, Scene as SceneSchema
from ...dependencies import get_current_active_user

router = APIRouter()


@router.get("/", response_model=List[SceneSchema])
def get_scenes(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    project_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Get list of scenes
    
    Args:
        skip: Number of scenes to skip
        limit: Maximum number of scenes to return
        project_id: Filter by project ID
        db: Database session
        current_user: Current authenticated user
    
    Returns:
        List of scenes
    """
    query = db.query(Scene)
    
    if project_id:
        query = query.filter(Scene.project_id == project_id)
    
    scenes = query.offset(skip).limit(limit).all()
    return scenes


@router.post("/", response_model=SceneSchema, status_code=status.HTTP_201_CREATED)
def create_scene(
    scene: SceneCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Create a new scene
    
    Args:
        scene: Scene data
        db: Database session
        current_user: Current authenticated user
    
    Returns:
        Created scene
    """
    # Verify project exists
    project = db.query(Project).filter(Project.id == scene.project_id).first()
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )
    
    # Check if scene name already exists in project
    existing_scene = db.query(Scene).filter(
        Scene.name == scene.name,
        Scene.project_id == scene.project_id
    ).first()
    if existing_scene:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Scene with this name already exists in the project"
        )
    
    db_scene = Scene(**scene.dict())
    db.add(db_scene)
    db.commit()
    db.refresh(db_scene)
    
    return db_scene


@router.get("/{scene_id}", response_model=SceneSchema)
def get_scene(
    scene_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Get scene by ID
    
    Args:
        scene_id: Scene ID
        db: Database session
        current_user: Current authenticated user
    
    Returns:
        Scene details
    """
    scene = db.query(Scene).filter(Scene.id == scene_id).first()
    if not scene:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Scene not found"
        )
    
    return scene


@router.put("/{scene_id}", response_model=SceneSchema)
def update_scene(
    scene_id: int,
    scene_update: SceneUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Update scene
    
    Args:
        scene_id: Scene ID
        scene_update: Scene update data
        db: Database session
        current_user: Current authenticated user
    
    Returns:
        Updated scene
    """
    scene = db.query(Scene).filter(Scene.id == scene_id).first()
    if not scene:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Scene not found"
        )
    
    # Check if new name already exists in project (if name is being updated)
    if scene_update.name and scene_update.name != scene.name:
        existing_scene = db.query(Scene).filter(
            Scene.name == scene_update.name,
            Scene.project_id == scene.project_id
        ).first()
        if existing_scene:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Scene with this name already exists in the project"
            )
    
    # Update scene fields
    update_data = scene_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(scene, field, value)
    
    db.commit()
    db.refresh(scene)
    
    return scene


@router.delete("/{scene_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_scene(
    scene_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Delete scene
    
    Args:
        scene_id: Scene ID
        db: Database session
        current_user: Current authenticated user
    """
    scene = db.query(Scene).filter(Scene.id == scene_id).first()
    if not scene:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Scene not found"
        )
    
    db.delete(scene)
    db.commit()
