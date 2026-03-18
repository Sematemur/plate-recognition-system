import base64
import io
import numpy as np
import pytest
from unittest.mock import patch, MagicMock
from PIL import Image


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_jpeg_bytes(width: int = 100, height: int = 60) -> bytes:
    """Return raw JPEG bytes for a solid-color image."""
    img = Image.new("RGB", (width, height), color=(128, 128, 128))
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    return buf.getvalue()


def _make_mock_yolo_result(boxes_data: list[dict]):
    """
    Build a mock YOLO result object.

    Each element of boxes_data must be a dict with keys:
        xyxy  : [x1, y1, x2, y2]  (floats)
        conf  : float
    """
    mock_result = MagicMock()

    if boxes_data:
        xyxy_array = np.array([[b["xyxy"]] for b in boxes_data], dtype=np.float32).reshape(-1, 4)
        conf_array = np.array([b["conf"] for b in boxes_data], dtype=np.float32)
    else:
        xyxy_array = np.empty((0, 4), dtype=np.float32)
        conf_array = np.empty((0,), dtype=np.float32)

    mock_boxes = MagicMock()
    mock_boxes.xyxy.cpu().numpy.return_value = xyxy_array
    mock_boxes.conf.cpu().numpy.return_value = conf_array

    mock_result.boxes = mock_boxes
    return mock_result


# ---------------------------------------------------------------------------
# Unit tests — PlateDetector (YOLO is mocked at import time)
# ---------------------------------------------------------------------------

class TestPlateDetector:
    """Unit tests for PlateDetector.detect()."""

    def test_detect_returns_plates_list(self):
        """Mock YOLO to return one detection; verify output format."""
        with patch("app.detector.YOLO") as MockYOLO:
            mock_yolo_instance = MagicMock()
            MockYOLO.return_value = mock_yolo_instance

            detection = {"xyxy": [10.0, 20.0, 80.0, 50.0], "conf": 0.91}
            mock_yolo_instance.return_value = [_make_mock_yolo_result([detection])]

            from app.detector import PlateDetector
            detector = PlateDetector("models/fake.pt")

            image_bytes = _make_jpeg_bytes()
            plates = detector.detect(image_bytes)

        assert isinstance(plates, list)
        assert len(plates) == 1

        plate = plates[0]
        assert "bbox" in plate
        assert "confidence" in plate
        assert "cropped_image" in plate

        # bbox values must be ints
        assert plate["bbox"] == [10, 20, 80, 50]

        # confidence is rounded to 4 decimal places
        assert plate["confidence"] == round(0.91, 4)

        # cropped_image must be valid base64-encoded JPEG
        raw = base64.b64decode(plate["cropped_image"])
        decoded_img = Image.open(io.BytesIO(raw))
        assert decoded_img.format == "JPEG"

    def test_detect_no_plates(self):
        """Mock YOLO to return no detections; verify empty list."""
        with patch("app.detector.YOLO") as MockYOLO:
            mock_yolo_instance = MagicMock()
            MockYOLO.return_value = mock_yolo_instance
            mock_yolo_instance.return_value = [_make_mock_yolo_result([])]

            from app.detector import PlateDetector
            detector = PlateDetector("models/fake.pt")

            image_bytes = _make_jpeg_bytes()
            plates = detector.detect(image_bytes)

        assert plates == []

    def test_detect_multiple_plates(self):
        """Mock YOLO to return two detections; verify both appear in output."""
        with patch("app.detector.YOLO") as MockYOLO:
            mock_yolo_instance = MagicMock()
            MockYOLO.return_value = mock_yolo_instance

            detections = [
                {"xyxy": [5.0, 5.0, 40.0, 25.0], "conf": 0.88},
                {"xyxy": [50.0, 30.0, 95.0, 55.0], "conf": 0.76},
            ]
            mock_yolo_instance.return_value = [_make_mock_yolo_result(detections)]

            from app.detector import PlateDetector
            detector = PlateDetector("models/fake.pt")

            image_bytes = _make_jpeg_bytes()
            plates = detector.detect(image_bytes)

        assert len(plates) == 2
        assert plates[0]["bbox"] == [5, 5, 40, 25]
        assert plates[1]["bbox"] == [50, 30, 95, 55]

    def test_detect_confidence_rounding(self):
        """Confidence values are rounded to 4 decimal places."""
        with patch("app.detector.YOLO") as MockYOLO:
            mock_yolo_instance = MagicMock()
            MockYOLO.return_value = mock_yolo_instance

            detection = {"xyxy": [10.0, 10.0, 50.0, 40.0], "conf": 0.123456789}
            mock_yolo_instance.return_value = [_make_mock_yolo_result([detection])]

            from app.detector import PlateDetector
            detector = PlateDetector("models/fake.pt")

            plates = detector.detect(_make_jpeg_bytes())

        assert plates[0]["confidence"] == round(0.123456789, 4)

    def test_detect_cropped_image_is_string(self):
        """cropped_image field must be a plain string (not bytes)."""
        with patch("app.detector.YOLO") as MockYOLO:
            mock_yolo_instance = MagicMock()
            MockYOLO.return_value = mock_yolo_instance

            detection = {"xyxy": [0.0, 0.0, 50.0, 30.0], "conf": 0.9}
            mock_yolo_instance.return_value = [_make_mock_yolo_result([detection])]

            from app.detector import PlateDetector
            detector = PlateDetector("models/fake.pt")

            plates = detector.detect(_make_jpeg_bytes())

        assert isinstance(plates[0]["cropped_image"], str)


# ---------------------------------------------------------------------------
# API tests — FastAPI endpoints (module-level detector instance is mocked)
# ---------------------------------------------------------------------------

class TestDetectEndpoint:
    """API-level tests for POST /detect."""

    def test_detect_endpoint_success(self, client, mock_detector):
        """POST /detect with a valid image; mock detector returns one plate."""
        fake_plate = {
            "bbox": [10, 20, 80, 50],
            "confidence": 0.91,
            "cropped_image": "fakeb64string==",
        }
        mock_detector.detect.return_value = [fake_plate]

        image_bytes = _make_jpeg_bytes()
        response = client.post(
            "/detect",
            files={"image": ("plate.jpg", image_bytes, "image/jpeg")},
        )

        assert response.status_code == 200
        body = response.json()
        assert body["success"] is True
        assert len(body["plates"]) == 1
        assert body["plates"][0]["bbox"] == [10, 20, 80, 50]
        assert body["plates"][0]["confidence"] == 0.91
        assert body["plates"][0]["cropped_image"] == "fakeb64string=="

        mock_detector.detect.assert_called_once_with(image_bytes)

    def test_detect_endpoint_no_plates(self, client, mock_detector):
        """POST /detect when detector returns no plates."""
        mock_detector.detect.return_value = []

        image_bytes = _make_jpeg_bytes()
        response = client.post(
            "/detect",
            files={"image": ("car.jpg", image_bytes, "image/jpeg")},
        )

        assert response.status_code == 200
        body = response.json()
        assert body["success"] is True
        assert body["plates"] == []

    def test_detect_endpoint_multiple_plates(self, client, mock_detector):
        """POST /detect when detector returns multiple plates."""
        fake_plates = [
            {"bbox": [5, 5, 40, 25], "confidence": 0.88, "cropped_image": "aaa=="},
            {"bbox": [50, 30, 95, 55], "confidence": 0.76, "cropped_image": "bbb=="},
        ]
        mock_detector.detect.return_value = fake_plates

        response = client.post(
            "/detect",
            files={"image": ("multi.jpg", _make_jpeg_bytes(), "image/jpeg")},
        )

        assert response.status_code == 200
        body = response.json()
        assert body["success"] is True
        assert len(body["plates"]) == 2

    def test_detect_endpoint_missing_file(self, client, mock_detector):
        """POST /detect without attaching a file should return 422."""
        response = client.post("/detect")
        assert response.status_code == 422

    def test_detect_endpoint_passes_raw_bytes_to_detector(self, client, mock_detector):
        """The endpoint must pass the raw file bytes (not a wrapper object) to detector."""
        mock_detector.detect.return_value = []
        image_bytes = _make_jpeg_bytes(200, 100)

        client.post(
            "/detect",
            files={"image": ("test.jpg", image_bytes, "image/jpeg")},
        )

        called_with = mock_detector.detect.call_args[0][0]
        assert isinstance(called_with, bytes)
        assert called_with == image_bytes


class TestHealthEndpoint:
    """API-level tests for GET /health."""

    def test_health_endpoint(self, client, mock_detector):
        """GET /health returns 200 with expected JSON body."""
        response = client.get("/health")

        assert response.status_code == 200
        body = response.json()
        assert body["status"] == "ok"
        assert body["service"] == "yolo-detection"

    def test_health_endpoint_does_not_call_detector(self, client, mock_detector):
        """GET /health must never invoke the detector."""
        client.get("/health")
        mock_detector.detect.assert_not_called()
