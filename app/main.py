from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse

from app.api.routers import (
    analytics,
    campaigns,
    communications,
    contacts,
    enrichment,
    health,
    leads,
    settings,
)
from app.core.config import BASE_DIR, get_settings
from app.core.security import AdminBasicAuthMiddleware
from app.db.models import Base
from app.db.session import engine


@asynccontextmanager
async def lifespan(_app: FastAPI):
    config = get_settings()
    if config.auto_create_schema and config.environment.lower() != "production":
        Base.metadata.create_all(bind=engine)
    yield


def create_app() -> FastAPI:
    config = get_settings()
    application = FastAPI(title=config.app_name, version="3.0.0", lifespan=lifespan)
    application.add_middleware(AdminBasicAuthMiddleware)
    application.add_middleware(
        CORSMiddleware,
        allow_origins=config.allowed_origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
        allow_headers=["Authorization", "Content-Type"],
    )

    application.include_router(health.router)
    application.include_router(analytics.router)
    application.include_router(leads.router)
    application.include_router(contacts.router)
    application.include_router(settings.router)
    application.include_router(communications.router)
    application.include_router(campaigns.router)
    application.include_router(enrichment.router)

    @application.middleware("http")
    async def security_headers(request, call_next):
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "camera=(), geolocation=(), payment=()"
        if config.environment.lower() == "production":
            response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        return response

    @application.get("/", response_class=HTMLResponse, include_in_schema=False)
    def dashboard() -> str:
        path = BASE_DIR / "static" / "index.html"
        return path.read_text(encoding="utf-8") if path.exists() else "<h1>LeadPulse Nexus</h1>"

    return application


app = create_app()
