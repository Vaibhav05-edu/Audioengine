"""
Projects API endpoints
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from ....database import get_db
from ....models import Project, User
from ....schemas import ProjectCreate, ProjectUpdate, Project as ProjectSchema
from ...dependencies import get_current_active_user

router = APIRouter()


@router.get("/", response_model=List[ProjectSchema])
def get_projects(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Get list of projects
    
    Args:
        skip: Number of projects to skip
        limit: Maximum number of projects to return
        db: Database session
        current_user: Current authenticated user
    
    Returns:
        List of projects
    """
    projects = db.query(Project).filter(Project.is_active == True).offset(skip).limit(limit).all()
    return projects


@router.post("/", response_model=ProjectSchema, status_code=status.HTTP_201_CREATED)
def create_project(
    project: ProjectCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Create a new project
    
    Args:
        project: Project data
        db: Database session
        current_user: Current authenticated user
    
    Returns:
        Created project
    """
    # Check if project name already exists
    existing_project = db.query(Project).filter(Project.name == project.name).first()
    if existing_project:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Project with this name already exists"
        )
    
    db_project = Project(**project.dict())
    db.add(db_project)
    db.commit()
    db.refresh(db_project)
    
    return db_project


@router.get("/{project_id}", response_model=ProjectSchema)
def get_project(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Get project by ID
    
    Args:
        project_id: Project ID
        db: Database session
        current_user: Current authenticated user
    
    Returns:
        Project details
    """
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )
    
    return project


@router.put("/{project_id}", response_model=ProjectSchema)
def update_project(
    project_id: int,
    project_update: ProjectUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Update project
    
    Args:
        project_id: Project ID
        project_update: Project update data
        db: Database session
        current_user: Current authenticated user
    
    Returns:
        Updated project
    """
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )
    
    # Check if new name already exists (if name is being updated)
    if project_update.name and project_update.name != project.name:
        existing_project = db.query(Project).filter(Project.name == project_update.name).first()
        if existing_project:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Project with this name already exists"
            )
    
    # Update project fields
    update_data = project_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(project, field, value)
    
    db.commit()
    db.refresh(project)
    
    return project


@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_project(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Delete project (soft delete)
    
    Args:
        project_id: Project ID
        db: Database session
        current_user: Current authenticated user
    """
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )
    
    # Soft delete - mark as inactive
    project.is_active = False
    db.commit()
