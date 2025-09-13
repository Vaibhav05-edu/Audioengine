"""
Prompt generation API endpoints
"""

from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field

from ....database import get_db
from ....models import Scene, FXPlan, User
from ....services.prompt_generator import PromptGenerator, FXPlanPrompts
from ....schemas import GeneratedPrompt, SceneAnalysis, FXPlanJSON
from ...dependencies import get_current_active_user

router = APIRouter()


class GeneratePromptsRequest(BaseModel):
    """Request model for prompt generation"""
    scene_id: int = Field(..., description="Scene ID to generate prompts for")
    regenerate: bool = Field(default=False, description="Regenerate prompts even if they exist")


class GeneratePromptsResponse(BaseModel):
    """Response model for prompt generation"""
    success: bool
    message: str
    scene_id: int
    fx_plan_id: Optional[int] = None
    prompts: Optional[FXPlanPrompts] = None


class OverridePromptRequest(BaseModel):
    """Request model for prompt override"""
    prompt_id: str = Field(..., description="ID of the prompt to override")
    new_prompt: str = Field(..., min_length=1, max_length=500, description="New prompt text")
    reason: Optional[str] = Field(None, max_length=255, description="Reason for override")


class OverridePromptResponse(BaseModel):
    """Response model for prompt override"""
    success: bool
    message: str
    prompt_id: str
    new_prompt: str
    reason: Optional[str] = None


class GetPromptsResponse(BaseModel):
    """Response model for getting prompts"""
    scene_id: int
    scene_name: str
    fx_plan_id: Optional[int]
    prompts: Optional[FXPlanPrompts]
    has_prompts: bool


@router.post("/generate", response_model=GeneratePromptsResponse)
def generate_prompts(
    request: GeneratePromptsRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Generate ambience and SFX prompts from scene analysis
    
    This endpoint analyzes scene headings and text to automatically generate
    ambience and SFX prompts using the PRD's starter templates. The generated
    prompts are stored in the FXPlan JSON structure.
    
    **Prompt Generation Features:**
    - Scene heading analysis (location, time, mood)
    - Text analysis (verbs, nouns, action words)
    - Sound cue extraction
    - Environment cue detection
    - Template-based prompt generation
    - Confidence scoring for each prompt
    
    **Template Categories:**
    - **Location-based**: Forest, city, beach, mountain, desert, rain, snow
    - **Time-based**: Morning, afternoon, evening, night
    - **Mood-based**: Tense, peaceful, mysterious, dramatic
    - **Action-based**: Walking, running, opening, closing, breaking
    - **Object-based**: Glass, metal, wood, paper sounds
    
    **Analysis Process:**
    1. Parse scene heading for location, time, and mood
    2. Extract linguistic elements (verbs, nouns, adjectives)
    3. Identify sound and environment cues
    4. Generate prompts using appropriate templates
    5. Store in FXPlan JSON with metadata
    
    Args:
        request: Prompt generation request parameters
        db: Database session
        current_user: Current authenticated user
    
    Returns:
        Generation response with prompts and FX plan ID
    
    Raises:
        HTTPException: 404 if scene not found, 400 if generation fails
    """
    # Get scene
    scene = db.query(Scene).filter(Scene.id == request.scene_id).first()
    if not scene:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Scene not found"
        )
    
    # Check if prompts already exist
    existing_fx_plan = db.query(FXPlan).filter(
        FXPlan.scene_id == request.scene_id,
        FXPlan.status == "pending"
    ).first()
    
    if existing_fx_plan and not request.regenerate:
        # Return existing prompts
        return GeneratePromptsResponse(
            success=True,
            message="Prompts already exist for this scene",
            scene_id=request.scene_id,
            fx_plan_id=existing_fx_plan.id,
            prompts=existing_fx_plan.effects_config.get("prompts") if existing_fx_plan.effects_config else None
        )
    
    try:
        # Initialize prompt generator
        generator = PromptGenerator()
        
        # Generate prompts from scene
        scene_heading = f"{scene.location or 'UNKNOWN'} - {scene.time_of_day or 'UNKNOWN'}"
        scene_text = scene.description or ""
        
        # If we have screenplay data, use it
        if hasattr(scene, 'screenplay_data') and scene.screenplay_data:
            # Extract dialogue and action from screenplay data
            dialogue_text = " ".join([d.get('text', '') for d in scene.screenplay_data.get('dialogue', [])])
            action_text = " ".join([a.get('text', '') for a in scene.screenplay_data.get('action', [])])
            scene_text = f"{scene_text} {dialogue_text} {action_text}".strip()
        
        # Generate prompts
        fx_plan_prompts = generator.generate_fx_plan_prompts(scene_heading, scene_text)
        fx_plan_prompts.scene_id = request.scene_id
        fx_plan_prompts.scene_name = scene.name
        
        # Create or update FX plan
        if existing_fx_plan and request.regenerate:
            # Update existing FX plan
            existing_fx_plan.effects_config = {
                "prompts": fx_plan_prompts.__dict__,
                "generated_at": fx_plan_prompts.generated_at.isoformat(),
                "last_updated": fx_plan_prompts.generated_at.isoformat()
            }
            fx_plan_id = existing_fx_plan.id
        else:
            # Create new FX plan
            fx_plan = FXPlan(
                name=f"Generated FX Plan for {scene.name}",
                description=f"Auto-generated FX plan for scene: {scene.name}",
                effects_config={
                    "prompts": fx_plan_prompts.__dict__,
                    "generated_at": fx_plan_prompts.generated_at.isoformat(),
                    "last_updated": fx_plan_prompts.generated_at.isoformat()
                },
                status="pending",
                scene_id=request.scene_id,
                project_id=scene.project_id
            )
            db.add(fx_plan)
            db.commit()
            db.refresh(fx_plan)
            fx_plan_id = fx_plan.id
        
        return GeneratePromptsResponse(
            success=True,
            message=f"Generated {len(fx_plan_prompts.ambience_prompts)} ambience and {len(fx_plan_prompts.sfx_prompts)} SFX prompts",
            scene_id=request.scene_id,
            fx_plan_id=fx_plan_id,
            prompts=fx_plan_prompts
        )
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Prompt generation failed: {str(e)}"
        )


@router.get("/scene/{scene_id}", response_model=GetPromptsResponse)
def get_scene_prompts(
    scene_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Get generated prompts for a scene
    
    This endpoint retrieves the generated ambience and SFX prompts for a scene,
    including analysis summary and manual overrides.
    
    Args:
        scene_id: Scene ID
        db: Database session
        current_user: Current authenticated user
    
    Returns:
        Scene prompts with metadata
    
    Raises:
        HTTPException: 404 if scene not found
    """
    # Get scene
    scene = db.query(Scene).filter(Scene.id == scene_id).first()
    if not scene:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Scene not found"
        )
    
    # Get FX plan with prompts
    fx_plan = db.query(FXPlan).filter(
        FXPlan.scene_id == scene_id,
        FXPlan.status == "pending"
    ).first()
    
    prompts = None
    if fx_plan and fx_plan.effects_config:
        prompts_data = fx_plan.effects_config.get("prompts")
        if prompts_data:
            # Convert dict back to FXPlanPrompts object
            prompts = FXPlanPrompts(**prompts_data)
    
    return GetPromptsResponse(
        scene_id=scene_id,
        scene_name=scene.name,
        fx_plan_id=fx_plan.id if fx_plan else None,
        prompts=prompts,
        has_prompts=prompts is not None
    )


@router.put("/override", response_model=OverridePromptResponse)
def override_prompt(
    request: OverridePromptRequest,
    scene_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Override a generated prompt with manual input
    
    This endpoint allows manual override of generated prompts with custom text.
    The override is stored in the FXPlan JSON and marked for tracking.
    
    **Override Features:**
    - Manual prompt replacement
    - Override reason tracking
    - Audit trail maintenance
    - Confidence adjustment
    
    Args:
        request: Override request parameters
        scene_id: Scene ID
        db: Database session
        current_user: Current authenticated user
    
    Returns:
        Override response with updated prompt
    
    Raises:
        HTTPException: 404 if scene/FX plan not found, 400 if override fails
    """
    # Get scene
    scene = db.query(Scene).filter(Scene.id == scene_id).first()
    if not scene:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Scene not found"
        )
    
    # Get FX plan
    fx_plan = db.query(FXPlan).filter(
        FXPlan.scene_id == scene_id,
        FXPlan.status == "pending"
    ).first()
    
    if not fx_plan or not fx_plan.effects_config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="FX plan not found for this scene"
        )
    
    try:
        # Get prompts data
        prompts_data = fx_plan.effects_config.get("prompts")
        if not prompts_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No prompts found in FX plan"
            )
        
        # Convert to FXPlanPrompts object
        prompts = FXPlanPrompts(**prompts_data)
        
        # Apply override
        generator = PromptGenerator()
        updated_prompts = generator.apply_manual_override(
            prompts, 
            request.prompt_id, 
            request.new_prompt, 
            request.reason
        )
        
        # Update FX plan
        fx_plan.effects_config["prompts"] = updated_prompts.__dict__
        fx_plan.effects_config["last_updated"] = updated_prompts.generated_at.isoformat()
        
        db.commit()
        
        return OverridePromptResponse(
            success=True,
            message="Prompt overridden successfully",
            prompt_id=request.prompt_id,
            new_prompt=request.new_prompt,
            reason=request.reason
        )
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Prompt override failed: {str(e)}"
        )


@router.get("/analysis/{scene_id}", response_model=SceneAnalysis)
def get_scene_analysis(
    scene_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Get scene analysis results
    
    This endpoint provides detailed scene analysis including extracted
    linguistic elements, sound cues, and environment cues.
    
    Args:
        scene_id: Scene ID
        db: Database session
        current_user: Current authenticated user
    
    Returns:
        Scene analysis results
    
    Raises:
        HTTPException: 404 if scene not found
    """
    # Get scene
    scene = db.query(Scene).filter(Scene.id == scene_id).first()
    if not scene:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Scene not found"
        )
    
    try:
        # Initialize prompt generator
        generator = PromptGenerator()
        
        # Analyze scene
        scene_heading = f"{scene.location or 'UNKNOWN'} - {scene.time_of_day or 'UNKNOWN'}"
        scene_text = scene.description or ""
        
        # If we have screenplay data, use it
        if hasattr(scene, 'screenplay_data') and scene.screenplay_data:
            dialogue_text = " ".join([d.get('text', '') for d in scene.screenplay_data.get('dialogue', [])])
            action_text = " ".join([a.get('text', '') for a in scene.screenplay_data.get('action', [])])
            scene_text = f"{scene_text} {dialogue_text} {action_text}".strip()
        
        # Perform analysis
        analysis = generator.analyzer.analyze_scene(scene_heading, scene_text)
        
        return analysis
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Scene analysis failed: {str(e)}"
        )


@router.get("/templates")
def get_prompt_templates(
    current_user: User = Depends(get_current_active_user)
):
    """
    Get available prompt templates
    
    This endpoint returns all available prompt templates organized by category.
    Useful for understanding what types of prompts can be generated.
    
    Args:
        current_user: Current authenticated user
    
    Returns:
        Available prompt templates
    """
    from ....services.prompt_generator import PromptTemplates
    
    templates = PromptTemplates()
    
    return {
        "ambience_templates": {
            "location": templates.AMBIENCE_TEMPLATES["location"],
            "time": templates.AMBIENCE_TEMPLATES["time"],
            "mood": templates.AMBIENCE_TEMPLATES["mood"]
        },
        "sfx_templates": {
            "action": templates.SFX_TEMPLATES["action"],
            "environment": templates.SFX_TEMPLATES["environment"],
            "objects": templates.SFX_TEMPLATES["objects"]
        },
        "surface_mappings": templates.SURFACE_MAPPINGS,
        "object_mappings": templates.OBJECT_MAPPINGS
    }


@router.delete("/scene/{scene_id}")
def clear_scene_prompts(
    scene_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Clear generated prompts for a scene
    
    This endpoint removes all generated prompts for a scene, allowing
    for fresh generation.
    
    Args:
        scene_id: Scene ID
        db: Database session
        current_user: Current authenticated user
    
    Returns:
        Success message
    
    Raises:
        HTTPException: 404 if scene not found
    """
    # Get scene
    scene = db.query(Scene).filter(Scene.id == scene_id).first()
    if not scene:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Scene not found"
        )
    
    # Get FX plan
    fx_plan = db.query(FXPlan).filter(
        FXPlan.scene_id == scene_id,
        FXPlan.status == "pending"
    ).first()
    
    if fx_plan:
        # Clear prompts from FX plan
        if fx_plan.effects_config:
            fx_plan.effects_config.pop("prompts", None)
            fx_plan.effects_config["last_updated"] = datetime.now().isoformat()
        
        db.commit()
    
    return {"success": True, "message": f"Cleared prompts for scene {scene_id}"}
