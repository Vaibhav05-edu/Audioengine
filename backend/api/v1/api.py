"""
API v1 router
"""

from fastapi import APIRouter

from .endpoints import projects, audio, scenes, fx_plans, assets, renders, workflow, screenplay, alignment, sfx, prompt_generation

api_router = APIRouter()

# Include endpoint routers
api_router.include_router(
    projects.router,
    prefix="/projects",
    tags=["projects"]
)

api_router.include_router(
    audio.router,
    prefix="/audio",
    tags=["audio"]
)

api_router.include_router(
    scenes.router,
    prefix="/scenes",
    tags=["scenes"]
)

api_router.include_router(
    fx_plans.router,
    prefix="/fx-plans",
    tags=["fx-plans"]
)

api_router.include_router(
    assets.router,
    prefix="/assets",
    tags=["assets"]
)

api_router.include_router(
    renders.router,
    prefix="/renders",
    tags=["renders"]
)

api_router.include_router(
    workflow.router,
    prefix="/workflow",
    tags=["workflow"]
)

api_router.include_router(
    screenplay.router,
    prefix="/screenplay",
    tags=["screenplay"]
)

api_router.include_router(
    alignment.router,
    prefix="/alignment",
    tags=["alignment"]
)

api_router.include_router(
    sfx.router,
    prefix="/sfx",
    tags=["sfx"]
)

api_router.include_router(
    prompt_generation.router,
    prefix="/prompts",
    tags=["prompt-generation"]
)
