"""
Renders API endpoints
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from ....database import get_db
from ....models import Render, Scene, FXPlan, Project, User
from ....schemas import RenderCreate, RenderUpdate, Render as RenderSchema
from ...dependencies import get_current_active_user

router = APIRouter()


@router.get("/", response_model=List[RenderSchema])
def get_renders(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    scene_id: Optional[int] = Query(None),
    fx_plan_id: Optional[int] = Query(None),
    project_id: Optional[int] = Query(None),
    status_filter: Optional[str] = Query(None),
    render_type: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Get list of renders
    
    Args:
        skip: Number of renders to skip
        limit: Maximum number of renders to return
        scene_id: Filter by scene ID
        fx_plan_id: Filter by FX plan ID
        project_id: Filter by project ID
        status_filter: Filter by status
        render_type: Filter by render type
        db: Database session
        current_user: Current authenticated user
    
    Returns:
        List of renders
    """
    query = db.query(Render)
    
    if scene_id:
        query = query.filter(Render.scene_id == scene_id)
    
    if fx_plan_id:
        query = query.filter(Render.fx_plan_id == fx_plan_id)
    
    if project_id:
        query = query.filter(Render.project_id == project_id)
    
    if status_filter:
        query = query.filter(Render.status == status_filter)
    
    if render_type:
        query = query.filter(Render.render_type == render_type)
    
    renders = query.offset(skip).limit(limit).all()
    return renders


@router.post("/", response_model=RenderSchema, status_code=status.HTTP_201_CREATED)
def create_render(
    render: RenderCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Create a new render
    
    Args:
        render: Render data
        db: Database session
        current_user: Current authenticated user
    
    Returns:
        Created render
    """
    # Verify scene exists
    scene = db.query(Scene).filter(Scene.id == render.scene_id).first()
    if not scene:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Scene not found"
        )
    
    # Verify project exists
    project = db.query(Project).filter(Project.id == render.project_id).first()
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )
    
    # Verify FX plan exists if provided
    if render.fx_plan_id:
        fx_plan = db.query(FXPlan).filter(FXPlan.id == render.fx_plan_id).first()
        if not fx_plan:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="FX plan not found"
            )
    
    # Check if render name already exists in scene
    existing_render = db.query(Render).filter(
        Render.name == render.name,
        Render.scene_id == render.scene_id
    ).first()
    if existing_render:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Render with this name already exists in the scene"
        )
    
    db_render = Render(**render.dict())
    db.add(db_render)
    db.commit()
    db.refresh(db_render)
    
    return db_render


@router.get("/{render_id}", response_model=RenderSchema)
def get_render(
    render_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Get render by ID
    
    Args:
        render_id: Render ID
        db: Database session
        current_user: Current authenticated user
    
    Returns:
        Render details
    """
    render = db.query(Render).filter(Render.id == render_id).first()
    if not render:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Render not found"
        )
    
    return render


@router.put("/{render_id}", response_model=RenderSchema)
def update_render(
    render_id: int,
    render_update: RenderUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Update render
    
    Args:
        render_id: Render ID
        render_update: Render update data
        db: Database session
        current_user: Current authenticated user
    
    Returns:
        Updated render
    """
    render = db.query(Render).filter(Render.id == render_id).first()
    if not render:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Render not found"
        )
    
    # Check if new name already exists in scene (if name is being updated)
    if render_update.name and render_update.name != render.name:
        existing_render = db.query(Render).filter(
            Render.name == render_update.name,
            Render.scene_id == render.scene_id
        ).first()
        if existing_render:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Render with this name already exists in the scene"
            )
    
    # Update render fields
    update_data = render_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(render, field, value)
    
    db.commit()
    db.refresh(render)
    
    return render


@router.delete("/{render_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_render(
    render_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Delete render
    
    Args:
        render_id: Render ID
        db: Database session
        current_user: Current authenticated user
    """
    render = db.query(Render).filter(Render.id == render_id).first()
    if not render:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Render not found"
        )
    
    db.delete(render)
    db.commit()
