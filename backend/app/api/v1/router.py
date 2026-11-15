from fastapi import APIRouter

from app.api.v1.endpoints import health
from app.experiments.router import router as experiments_router

api_router = APIRouter()

api_router.include_router(health.router)
api_router.include_router(experiments_router)
