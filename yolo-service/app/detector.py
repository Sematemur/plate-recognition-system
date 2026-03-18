import base64
import io
import logging

from PIL import Image
from ultralytics import YOLO

from app.config import settings

logger = logging.getLogger(__name__)


class PlateDetector:
    def __init__(self, model_path: str):
        self.model = YOLO(model_path)
        logger.info("YOLO model loaded from %s", model_path)

    def detect(self, image_bytes: bytes) -> list[dict]:
        image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
        results = self.model(image, conf=settings.yolo_confidence_threshold)
        plates = []
        for result in results:
            boxes = result.boxes
            xyxy = boxes.xyxy.cpu().numpy()
            confs = boxes.conf.cpu().numpy()
            for i in range(len(xyxy)):
                x1, y1, x2, y2 = map(int, xyxy[i])
                cropped = image.crop((x1, y1, x2, y2))
                buf = io.BytesIO()
                cropped.save(buf, format="JPEG")
                cropped_b64 = base64.b64encode(buf.getvalue()).decode("utf-8")
                plates.append({
                    "bbox": [x1, y1, x2, y2],
                    "confidence": round(float(confs[i]), 4),
                    "cropped_image": cropped_b64,
                })
        return plates
