import logging

import httpx
from sqlalchemy.orm import Session

from app.config import settings
from app.models import Vehicle, RecognitionLog
from app.plate_utils import normalize_plate
from app.schemas import VehicleResponse

logger = logging.getLogger(__name__)

# Reusable HTTP clients — avoids creating/destroying TCP connections per request
_yolo_client: httpx.AsyncClient | None = None
_ocr_client: httpx.AsyncClient | None = None


async def _get_yolo_client() -> httpx.AsyncClient:
    global _yolo_client
    if _yolo_client is None or _yolo_client.is_closed:
        _yolo_client = httpx.AsyncClient(
            base_url=settings.yolo_service_url,
            timeout=settings.yolo_timeout,
        )
    return _yolo_client


async def _get_ocr_client() -> httpx.AsyncClient:
    global _ocr_client
    if _ocr_client is None or _ocr_client.is_closed:
        _ocr_client = httpx.AsyncClient(
            base_url=settings.ocr_service_url,
            timeout=settings.ocr_timeout,
        )
    return _ocr_client


async def close_http_clients():
    """Call on shutdown to cleanly close HTTP connection pools."""
    global _yolo_client, _ocr_client
    if _yolo_client and not _yolo_client.is_closed:
        await _yolo_client.aclose()
        _yolo_client = None
    if _ocr_client and not _ocr_client.is_closed:
        await _ocr_client.aclose()
        _ocr_client = None


async def call_yolo_service(image_bytes: bytes) -> dict:
    client = await _get_yolo_client()
    response = await client.post(
        "/detect",
        files={"image": ("image.jpg", image_bytes, "image/jpeg")},
    )
    response.raise_for_status()
    return response.json()


async def call_ocr_service(image_b64: str) -> dict:
    client = await _get_ocr_client()
    response = await client.post(
        "/recognize",
        json={"image": image_b64},
    )
    response.raise_for_status()
    return response.json()


async def recognize_plate(
    image_bytes: bytes,
    image_name: str,
    db: Session,
) -> dict:
    """Full recognition pipeline: YOLO detect -> OCR read -> DB lookup -> log."""
    # Step 1: YOLO detection
    try:
        yolo_result = await call_yolo_service(image_bytes)
    except httpx.HTTPError:
        logger.error("YOLO service call failed", exc_info=True)
        return {
            "success": False,
            "error": "service_unavailable",
            "detail": "Detection service is temporarily unavailable",
        }

    plates = yolo_result.get("plates", [])
    if not plates:
        return {
            "success": False,
            "error": "no_plate_detected",
            "detail": "No license plate detected in the image",
        }

    # Step 2: Best plate + OCR
    best_plate = max(plates, key=lambda p: p["confidence"])
    det_confidence = best_plate["confidence"]

    try:
        ocr_result = await call_ocr_service(best_plate["cropped_image"])
    except httpx.HTTPError:
        logger.error("OCR service call failed", exc_info=True)
        return {
            "success": False,
            "error": "service_unavailable",
            "detail": "Recognition service is temporarily unavailable",
        }

    plate_text = ocr_result.get("plate_text", "")
    ocr_confidence = ocr_result.get("confidence", 0.0)

    # Step 3: DB lookup
    normalized = normalize_plate(plate_text)
    vehicle = db.query(Vehicle).filter(Vehicle.plate_number == normalized).first()
    is_known = vehicle is not None

    # Step 4: Save recognition log with rollback on failure
    log = RecognitionLog(
        image_path=image_name,
        plate_detected=plate_text,
        vehicle_id=vehicle.id if vehicle else None,
        is_known=is_known,
        confidence=ocr_confidence,
        det_confidence=det_confidence,
    )
    try:
        db.add(log)
        db.commit()
        db.refresh(log)
    except Exception:
        db.rollback()
        logger.error("Failed to save recognition log", exc_info=True)
        return {
            "success": False,
            "error": "internal_error",
            "detail": "Failed to save recognition result",
        }

    vehicle_data = None
    if vehicle:
        vehicle_data = VehicleResponse.model_validate(vehicle)

    return {
        "success": True,
        "plate_text": plate_text,
        "confidence": ocr_confidence,
        "detection_confidence": det_confidence,
        "is_known": is_known,
        "vehicle": vehicle_data,
        "log_id": log.id,
    }
