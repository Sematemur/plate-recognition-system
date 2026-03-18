import logging
from contextlib import asynccontextmanager

import httpx
from fastapi import FastAPI
from pydantic import BaseModel

from app.config import settings
from app.recognizer import PlateRecognizer

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)
logger = logging.getLogger(__name__)

recognizer = PlateRecognizer(
    litellm_base_url=settings.litellm_base_url,
    model=settings.litellm_model,
    api_key=settings.litellm_api_key,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield
    await recognizer.close()
    logger.info("HTTP client closed")


app = FastAPI(title="OCR Plate Recognition Service", lifespan=lifespan)


class RecognizeRequest(BaseModel):
    image: str  # base64 encoded


@app.post("/recognize")
async def recognize_plate(request: RecognizeRequest):
    result = await recognizer.recognize(request.image)
    return {"success": True, **result}


@app.get("/health")
async def health():
    try:
        async with httpx.AsyncClient(timeout=settings.litellm_timeout) as client:
            r = await client.get(f"{settings.litellm_base_url}/health")
            litellm_ok = r.status_code == 200
    except Exception:
        litellm_ok = False

    status = "ok" if litellm_ok else "degraded"
    return {
        "status": status,
        "service": "ocr-recognition",
        "litellm": "ok" if litellm_ok else "unavailable",
    }
