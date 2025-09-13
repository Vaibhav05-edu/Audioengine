"""
FX Plans API endpoints
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from ....database import get_db
from ....models import FXPlan, Scene, Project, User
from ....schemas import FXPlanCreate, FXPlanUpdate, FXPlan as FXPlanSchema
from ...dependencies import get_current_active_user

router = APIRouter()


@router.get("/", response_model=List[FXPlanSchema])
def get_fx_plans(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    scene_id: Optional[int] = Query(None),
    project_id: Optional[int] = Query(None),
    status_filter: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Get list of FX plans
    
    Args:
        skip: Number of plans to skip
        limit: Maximum number of plans to return
        scene_id: Filter by scene ID
        project_id: Filter by project ID
        status_filter: Filter by status
        db: Database session
        current_user: Current authenticated user
    
    Returns:
        List of FX plans
    """
    query = db.query(FXPlan)
    
    if scene_id:
        query = query.filter(FXPlan.scene_id == scene_id)
    
    if project_id:
        query = query.filter(FXPlan.project_id == project_id)
    
    if status_filter:
        query = query.filter(FXPlan.status == status_filter)
    
    fx_plans = query.offset(skip).limit(limit).all()
    return fx_plans


@router.post("/", response_model=FXPlanSchema, status_code=status.HTTP_201_CREATED)
def create_fx_plan(
    fx_plan: FXPlanCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Create a new FX plan
    
    Args:
        fx_plan: FX plan data
        db: Database session
        current_user: Current authenticated user
    
    Returns:
        Created FX plan
    """
    # Verify scene exists
    scene = db.query(Scene).filter(Scene.id == fx_plan.scene_id).first()
    if not scene:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Scene not found"
        )
    
    # Verify project exists
    project = db.query(Project).filter(Project.id == fx_plan.project_id).first()
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )
    
    # Check if FX plan name already exists in scene
    existing_plan = db.query(FXPlan).filter(
        FXPlan.name == fx_plan.name,
        FXPlan.scene_id == fx_plan.scene_id
    ).first()
    if existing_plan:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="FX plan with this name already exists in the scene"
        )
    
    db_fx_plan = FXPlan(**fx_plan.dict())
    db.add(db_fx_plan)
    db.commit()
    db.refresh(db_fx_plan)
    
    return db_fx_plan


@router.get("/{fx_plan_id}", response_model=FXPlanSchema)
def get_fx_plan(
    fx_plan_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Get FX plan by ID
    
    Args:
        fx_plan_id: FX plan ID
        db: Database session
        current_user: Current authenticated user
    
    Returns:
        FX plan details
    """
    fx_plan = db.query(FXPlan).filter(FXPlan.id == fx_plan_id).first()
    if not fx_plan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="FX plan not found"
        )
    
    return fx_plan


@router.put("/{fx_plan_id}", response_model=FXPlanSchema)
def update_fx_plan(
    fx_plan_id: int,
    fx_plan_update: FXPlanUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Update FX plan
    
    Args:
        fx_plan_id: FX plan ID
        fx_plan_update: FX plan update data
        db: Database session
        current_user: Current authenticated user
    
    Returns:
        Updated FX plan
    """
    fx_plan = db.query(FXPlan).filter(FXPlan.id == fx_plan_id).first()
    if not fx_plan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="FX plan not found"
        )
    
    # Check if new name already exists in scene (if name is being updated)
    if fx_plan_update.name and fx_plan_update.name != fx_plan.name:
        existing_plan = db.query(FXPlan).filter(
            FXPlan.name == fx_plan_update.name,
            FXPlan.scene_id == fx_plan.scene_id
        ).first()
        if existing_plan:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="FX plan with this name already exists in the scene"
            )
    
    # Update FX plan fields
    update_data = fx_plan_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(fx_plan, field, value)
    
    db.commit()
    db.refresh(fx_plan)
    
    return fx_plan


@router.delete("/{fx_plan_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_fx_plan(
    fx_plan_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Delete FX plan
    
    Args:
        fx_plan_id: FX plan ID
        db: Database session
        current_user: Current authenticated user
    """
    fx_plan = db.query(FXPlan).filter(FXPlan.id == fx_plan_id).first()
    if not fx_plan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="FX plan not found"
        )
    
    db.delete(fx_plan)
    db.commit()
