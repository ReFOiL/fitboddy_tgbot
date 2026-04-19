from fastapi import APIRouter

from src.presentation.web_admin.api.v1.exercises import router as exercises_router
from src.presentation.web_admin.api.v1.workout_templates import router as workout_templates_router
from src.presentation.web_admin.api.v1.uploads import router as uploads_router
from src.presentation.web_admin.api.v1.muscles import router as muscles_router
from src.presentation.web_admin.api.v1.contraindications import router as contraindications_router
from src.presentation.web_admin.api.v1.equipment import router as equipment_router

api_router = APIRouter(prefix="/api/v1", tags=["api"])
api_router.include_router(exercises_router, prefix="/admin", tags=["exercises"])
api_router.include_router(workout_templates_router, prefix="/admin", tags=["workout_templates"])
api_router.include_router(uploads_router, prefix="/admin", tags=["uploads"])
api_router.include_router(muscles_router, prefix="/admin", tags=["muscles"])
api_router.include_router(contraindications_router, prefix="/admin", tags=["contraindications"])
api_router.include_router(equipment_router, prefix="/admin", tags=["equipment"])
# Gender API удален - пол хранится как строка в workout_template_allowed_genders
