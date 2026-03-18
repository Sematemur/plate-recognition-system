import logging

from fastapi import FastAPI, File, UploadFile
from fastapi.responses import JSONResponse

from app.config import settings
from app.detector import PlateDetector

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)
logger = logging.getLogger(__name__)

app = FastAPI(title="YOLO Plate Detection Service")
detector = PlateDetector(settings.yolo_model_path)


@app.post("/detect")
async def detect_plates(image: UploadFile = File(...)):
    contents = await image.read()

    if len(contents) == 0:
        return JSONResponse(status_code=400, content={"error": "Empty image"})

    if len(contents) > settings.max_image_size_bytes:
        return JSONResponse(status_code=400, content={"error": "Image too large"})

    plates = detector.detect(contents)
    return {"success": True, "plates": plates}


@app.get("/health")
async def health():
    model_loaded = detector.model is not None
    return {
        "status": "ok" if model_loaded else "error",
        "service": "yolo-detection",
        "model_loaded": model_loaded,
    }
