import pytest
from unittest.mock import AsyncMock, patch, MagicMock
import httpx
from app.services import call_yolo_service, call_ocr_service


@pytest.mark.asyncio
async def test_call_yolo_service_success():
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "success": True,
        "plates": [{"bbox": [1, 2, 3, 4], "confidence": 0.95, "cropped_image": "abc"}],
    }
    mock_response.raise_for_status = MagicMock()

    mock_client = AsyncMock(spec=httpx.AsyncClient)
    mock_client.post.return_value = mock_response
    mock_client.is_closed = False

    with patch("app.services._yolo_client", mock_client):
        result = await call_yolo_service(b"fake_image_bytes")
        assert result["success"] is True
        assert len(result["plates"]) == 1


@pytest.mark.asyncio
async def test_call_ocr_service_success():
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "success": True,
        "plate_text": "34 ABC 123",
        "confidence": 0.9,
    }
    mock_response.raise_for_status = MagicMock()

    mock_client = AsyncMock(spec=httpx.AsyncClient)
    mock_client.post.return_value = mock_response
    mock_client.is_closed = False

    with patch("app.services._ocr_client", mock_client):
        result = await call_ocr_service("base64imagedata")
        assert result["plate_text"] == "34 ABC 123"


@pytest.mark.asyncio
async def test_call_yolo_service_unavailable():
    mock_client = AsyncMock(spec=httpx.AsyncClient)
    mock_client.post.side_effect = httpx.ConnectError("Connection refused")
    mock_client.is_closed = False

    with patch("app.services._yolo_client", mock_client):
        with pytest.raises(httpx.HTTPError):
            await call_yolo_service(b"fake_image_bytes")
