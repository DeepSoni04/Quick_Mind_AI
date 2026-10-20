import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.core.config import settings
from app.core.database import close_mongo_connection, connect_to_mongo
from app.routers import admin, auth, databases, history, queries, sessions, settings as settings_router
from app.schemas.common import HealthResponse

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("querymind.main")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application startup and shutdown lifecycle events."""
    logger.info(f"Starting {settings.APP_NAME} backend in {settings.ENVIRONMENT} mode...")
    await connect_to_mongo()
    yield
    logger.info(f"Shutting down {settings.APP_NAME} backend...")
    await close_mongo_connection()


app = FastAPI(
    title=settings.APP_NAME,
    description="Natural Language Database Assistant production API backend",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)

# CORS Configuration
origins = settings.CORS_ORIGINS if isinstance(settings.CORS_ORIGINS, list) else [settings.CORS_ORIGINS]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Catch unhandled exceptions and return safe user-facing message without exposing stack traces."""
    logger.error(f"Unhandled exception on {request.method} {request.url.path}: {exc}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "An internal server error occurred. Please try again later."}
    )


# Health Check
@app.get("/health", response_model=HealthResponse, tags=["Health"])
async def health_check():
    return HealthResponse(status="ok")


# Include Routers
app.include_router(auth.router)
app.include_router(databases.router)
app.include_router(queries.router)
app.include_router(sessions.router)
app.include_router(history.router)
app.include_router(settings_router.router)
app.include_router(admin.router)
