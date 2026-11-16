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
    """Manage application startup and shutdown lifecycle events safely."""
    logger.info(f"Starting {settings.APP_NAME} backend in {settings.ENVIRONMENT} mode...")
    try:
        await connect_to_mongo()
    except Exception as e:
        logger.warning(f"MongoDB connection notice during startup: {e}")
    yield
    try:
        await close_mongo_connection()
    except Exception as e:
        logger.warning(f"MongoDB close notice during shutdown: {e}")


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
if "https://quickmind-frontend.vercel.app" not in origins:
    origins.append("https://quickmind-frontend.vercel.app")

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_origin_regex=r"https://.*\.vercel\.app",
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


@app.middleware("http")
async def normalize_vercel_path(request: Request, call_next):
    """Normalize Vercel serverless request path if entrypoint prefix is present."""
    path = request.scope.get("path", "")
    if path.startswith("/api/index.py/"):
        request.scope["path"] = path[len("/api/index.py"):]
    elif path.startswith("/api/index/"):
        request.scope["path"] = path[len("/api/index"):]
    return await call_next(request)


# Health Check endpoints matching all routing permutations
@app.get("/", response_model=HealthResponse, tags=["Health"])
@app.get("/health", response_model=HealthResponse, tags=["Health"])
@app.get("/api", response_model=HealthResponse, tags=["Health"])
@app.get("/api/health", response_model=HealthResponse, tags=["Health"])
@app.get("/api/index.py", response_model=HealthResponse, tags=["Health"])
@app.get("/api/index", response_model=HealthResponse, tags=["Health"])
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
