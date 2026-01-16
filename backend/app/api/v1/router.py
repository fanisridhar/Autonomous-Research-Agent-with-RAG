"""API v1 router combining all endpoints."""
from fastapi import APIRouter
from app.api.v1.endpoints import auth, projects, documents, qa, export

api_router = APIRouter()

# Include all endpoint routers
api_router.include_router(auth.router, prefix="/auth", tags=["authentication"])
api_router.include_router(projects.router, prefix="/projects", tags=["projects"])
api_router.include_router(documents.router, prefix="/documents", tags=["documents"])
api_router.include_router(qa.router, prefix="/qa", tags=["qa"])
api_router.include_router(export.router, prefix="/export", tags=["export"])

