from fastapi import APIRouter

from app.api import endpoints

api_router = APIRouter()
api_router.include_router(endpoints.router)
