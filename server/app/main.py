from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .database import Base, ENGINE


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=ENGINE)
    yield


app = FastAPI(
    title="TransitShield AI API",
    description="AI-powered safety operations and incident investigation platform for public transportation",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from .routes import (  # noqa: E402
    camera_router,
    incident_router,
    investigation_router,
    officer_router,
    report_router,
    risk_router,
    system_router,
)

app.include_router(camera_router)
app.include_router(incident_router)
app.include_router(officer_router)
app.include_router(report_router)
app.include_router(risk_router)
app.include_router(system_router)
