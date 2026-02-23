# Routers package — all domain APIRouter instances re-exported for main.py
from .health import router as health_router
from .auth import router as auth_router
from .admin import router as admin_router
from .users import router as users_router
from .reports import router as reports_router
from .jobs import router as jobs_router
from .properties import router as properties_router
from .vehicles import router as vehicles_router
from .ocr import router as ocr_router
from .autocomplete import router as autocomplete_router
from .maps import router as maps_router
from .locality import router as locality_router
from .narratives import router as narratives_router

__all__ = [
    "health_router",
    "auth_router",
    "admin_router",
    "users_router",
    "reports_router",
    "jobs_router",
    "properties_router",
    "vehicles_router",
    "ocr_router",
    "autocomplete_router",
    "maps_router",
    "locality_router",
    "narratives_router",
]
