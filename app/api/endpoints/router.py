from fastapi import APIRouter

from app.api.endpoints.upload import router as upload_router
from app.api.endpoints.assessment import router as assessment_router
from app.api.endpoints.analysis import router as analysis_router
from app.api.endpoints.chat import router as chat_router
from app.api.endpoints.dashboard import router as dashboard_router

router = APIRouter()

router.include_router(upload_router)
router.include_router(assessment_router)
router.include_router(analysis_router)
router.include_router(chat_router)
router.include_router(dashboard_router)
