from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI

from database import engine
from app.models.service_request import ServiceRequest
from app.service_requests.router import router as request_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Create database tables if they do not exist
    ServiceRequest.metadata.create_all(engine)
    yield


app = FastAPI(
    title="CampusFix API",
    lifespan=lifespan,
    docs_url="/api/docs",
    openapi_url="/api/openapi.json",
)


# Register service request endpoints
app.include_router(request_router)


# Health check
@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


# Serve the built React frontend
FRONTEND_DIR = Path(__file__).resolve().parent.parent / "frontend" / "dist"

if FRONTEND_DIR.is_dir():
    app.frontend("/", directory=FRONTEND_DIR)
