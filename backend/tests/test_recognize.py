import pytest
from unittest.mock import AsyncMock, patch
from PIL import Image
import io

def _make_test_image() -> bytes:
    img = Image.new("RGB", (400, 300), "white")
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    return buf.getvalue()

@patch("app.services.call_ocr_service", new_callable=AsyncMock)
@patch("app.services.call_yolo_service", new_callable=AsyncMock)
def test_recognize_known_vehicle(mock_yolo, mock_ocr, client, db):
    from app.models import Vehicle
    vehicle = Vehicle(
        plate_number="34ABC123",
        plate_display="34 ABC 123",
        fuel_type="dizel",
        brand="Toyota",
        model="Corolla",
        color="Beyaz",
    )
    db.add(vehicle)
    db.commit()

    mock_yolo.return_value = {
        "success": True,
        "plates": [{"bbox": [1, 2, 3, 4], "confidence": 0.95, "cropped_image": "dGVzdA=="}],
    }
    mock_ocr.return_value = {
        "success": True,
        "plate_text": "34 ABC 123",
        "confidence": 0.9,
    }

    response = client.post(
        "/api/recognize",
        files={"image": ("test.jpg", _make_test_image(), "image/jpeg")},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["is_known"] is True
    assert data["vehicle"]["fuel_type"] == "dizel"
    assert data["plate_text"] == "34 ABC 123"

@patch("app.services.call_ocr_service", new_callable=AsyncMock)
@patch("app.services.call_yolo_service", new_callable=AsyncMock)
def test_recognize_unknown_vehicle(mock_yolo, mock_ocr, client, db):
    mock_yolo.return_value = {
        "success": True,
        "plates": [{"bbox": [1, 2, 3, 4], "confidence": 0.95, "cropped_image": "dGVzdA=="}],
    }
    mock_ocr.return_value = {
        "success": True,
        "plate_text": "06 AB 789",
        "confidence": 0.85,
    }

    response = client.post(
        "/api/recognize",
        files={"image": ("test.jpg", _make_test_image(), "image/jpeg")},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["is_known"] is False
    assert data["vehicle"] is None

@patch("app.services.call_yolo_service", new_callable=AsyncMock)
def test_recognize_no_plate_detected(mock_yolo, client, db):
    mock_yolo.return_value = {"success": True, "plates": []}

    response = client.post(
        "/api/recognize",
        files={"image": ("test.jpg", _make_test_image(), "image/jpeg")},
    )
    assert response.status_code == 404
    data = response.json()
    assert data["error"] == "no_plate_detected"
