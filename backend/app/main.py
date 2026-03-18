import logging
from contextlib import asynccontextmanager

import httpx
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import text

from app.config import settings
from app.database import engine, Base, SessionLocal
from app.routes import recognize, vehicles, logs, feed
from app.services import close_http_clients

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables created")
    yield
    # Shutdown: close reusable HTTP clients
    await close_http_clients()
    engine.dispose()
    logger.info("Connections closed")


app = FastAPI(title="Plate Recognition Backend", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(recognize.router)
app.include_router(vehicles.router)
app.include_router(logs.router)
app.include_router(feed.router)


@app.get("/health")
async def health():
    checks = {"backend": "ok"}

    db = SessionLocal()
    try:
        db.execute(text("SELECT 1"))
        checks["database"] = "ok"
    except Exception:
        checks["database"] = "unavailable"
    finally:
        db.close()

    async with httpx.AsyncClient(timeout=settings.health_check_timeout) as client:
        for name, url in [
            ("yolo", settings.yolo_service_url),
            ("ocr", settings.ocr_service_url),
        ]:
            try:
                r = await client.get(f"{url}/health")
                checks[name] = "ok" if r.status_code == 200 else "degraded"
            except Exception:
                checks[name] = "unavailable"

    status = "ok" if all(v == "ok" for v in checks.values()) else "degraded"
    status_code = 200 if status == "ok" else 503
    return JSONResponse(
        status_code=status_code,
        content={"status": status, "checks": checks},
    )
