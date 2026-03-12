from fastapi import APIRouter

from spirit.api import thoughts, categories, auth, insights, export

api_router = APIRouter()

api_router.include_router(auth.router)
api_router.include_router(thoughts.router)
api_router.include_router(categories.router)
api_router.include_router(insights.router)
api_router.include_router(export.router)
