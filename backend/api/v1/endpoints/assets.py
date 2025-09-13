"""
Assets API endpoints
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from ....database import get_db
from ....models import Asset, Scene, Project, User
from ....schemas import AssetCreate, AssetUpdate, Asset as AssetSchema
from ...dependencies import get_current_active_user

router = APIRouter()


@router.get("/", response_model=List[AssetSchema])
def get_assets(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    scene_id: Optional[int] = Query(None),
    project_id: Optional[int] = Query(None),
    asset_type: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Get list of assets
    
    Args:
        skip: Number of assets to skip
        limit: Maximum number of assets to return
        scene_id: Filter by scene ID
        project_id: Filter by project ID
        asset_type: Filter by asset type
        db: Database session
        current_user: Current authenticated user
    
    Returns:
        List of assets
    """
    query = db.query(Asset)
    
    if scene_id:
        query = query.filter(Asset.scene_id == scene_id)
    
    if project_id:
        query = query.filter(Asset.project_id == project_id)
    
    if asset_type:
        query = query.filter(Asset.asset_type == asset_type)
    
    assets = query.offset(skip).limit(limit).all()
    return assets


@router.post("/", response_model=AssetSchema, status_code=status.HTTP_201_CREATED)
def create_asset(
    asset: AssetCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Create a new asset
    
    Args:
        asset: Asset data
        db: Database session
        current_user: Current authenticated user
    
    Returns:
        Created asset
    """
    # Verify scene exists
    scene = db.query(Scene).filter(Scene.id == asset.scene_id).first()
    if not scene:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Scene not found"
        )
    
    # Verify project exists
    project = db.query(Project).filter(Project.id == asset.project_id).first()
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )
    
    # Check if asset name already exists in scene
    existing_asset = db.query(Asset).filter(
        Asset.name == asset.name,
        Asset.scene_id == asset.scene_id
    ).first()
    if existing_asset:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Asset with this name already exists in the scene"
        )
    
    db_asset = Asset(**asset.dict())
    db.add(db_asset)
    db.commit()
    db.refresh(db_asset)
    
    return db_asset


@router.get("/{asset_id}", response_model=AssetSchema)
def get_asset(
    asset_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Get asset by ID
    
    Args:
        asset_id: Asset ID
        db: Database session
        current_user: Current authenticated user
    
    Returns:
        Asset details
    """
    asset = db.query(Asset).filter(Asset.id == asset_id).first()
    if not asset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Asset not found"
        )
    
    return asset


@router.put("/{asset_id}", response_model=AssetSchema)
def update_asset(
    asset_id: int,
    asset_update: AssetUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Update asset
    
    Args:
        asset_id: Asset ID
        asset_update: Asset update data
        db: Database session
        current_user: Current authenticated user
    
    Returns:
        Updated asset
    """
    asset = db.query(Asset).filter(Asset.id == asset_id).first()
    if not asset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Asset not found"
        )
    
    # Check if new name already exists in scene (if name is being updated)
    if asset_update.name and asset_update.name != asset.name:
        existing_asset = db.query(Asset).filter(
            Asset.name == asset_update.name,
            Asset.scene_id == asset.scene_id
        ).first()
        if existing_asset:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Asset with this name already exists in the scene"
            )
    
    # Update asset fields
    update_data = asset_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(asset, field, value)
    
    db.commit()
    db.refresh(asset)
    
    return asset


@router.delete("/{asset_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_asset(
    asset_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Delete asset
    
    Args:
        asset_id: Asset ID
        db: Database session
        current_user: Current authenticated user
    """
    asset = db.query(Asset).filter(Asset.id == asset_id).first()
    if not asset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Asset not found"
        )
    
    db.delete(asset)
    db.commit()
