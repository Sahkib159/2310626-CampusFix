
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI

from database import engine

from app.models.service_request import ServiceRequest
from app.models.group import Group, GroupMember
from app.models.audit_log import AuditLog

from app.service_requests.router import router as request_router
from app.auth.router import router as auth_router
from app.staff.router import router as staff_router
from app.groups.router import router as group_router
from app.admin.router import router as admin_router
from app.audit.router import router as audit_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    ServiceRequest.metadata.create_all(engine)
    yield


app = FastAPI(
    title="CampusFix API",
    lifespan=lifespan,
    docs_url="/api/docs",
    openapi_url="/api/openapi.json",
)


app.include_router(request_router)
app.include_router(auth_router)
app.include_router(staff_router)
app.include_router(group_router)
app.include_router(admin_router)
app.include_router(audit_router)


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


FRONTEND_DIR = (
    Path(__file__).resolve().parent.parent
    / "frontend"
    / "dist"
)

if FRONTEND_DIR.is_dir():
    app.frontend("/", directory=FRONTEND_DIR)
