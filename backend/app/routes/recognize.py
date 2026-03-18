import logging

from fastapi import APIRouter, File, UploadFile, Depends
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.schemas import RecognizeResponse, ErrorResponse
from app.services import recognize_plate

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post(
    "/api/recognize",
    responses={400: {"model": ErrorResponse}, 404: {"model": ErrorResponse}, 503: {"model": ErrorResponse}},
)
async def recognize(
    image: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    image_bytes = await image.read()

    if len(image_bytes) == 0:
        return JSONResponse(
            status_code=400,
            content=ErrorResponse(error="invalid_image", detail="Uploaded file is empty").model_dump(),
        )

    if len(image_bytes) > settings.max_image_size_bytes:
        return JSONResponse(
            status_code=400,
            content=ErrorResponse(
                error="image_too_large",
                detail=f"Image exceeds {settings.max_image_size_bytes // (1024 * 1024)}MB limit",
            ).model_dump(),
        )

    if image.content_type and image.content_type not in settings.allowed_content_types:
        return JSONResponse(
            status_code=400,
            content=ErrorResponse(error="invalid_image_type", detail="Unsupported image format").model_dump(),
        )

    result = await recognize_plate(image_bytes, image.filename or "upload", db)

    if not result.get("success"):
        status_code = 404 if result["error"] == "no_plate_detected" else 503
        return JSONResponse(
            status_code=status_code,
            content=ErrorResponse(error=result["error"], detail=result["detail"]).model_dump(),
        )

    return RecognizeResponse(
        plate_text=result["plate_text"],
        is_known=result["is_known"],
        vehicle=result["vehicle"],
        log_id=result["log_id"],
    )
