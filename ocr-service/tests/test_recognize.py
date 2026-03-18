import pytest
from unittest.mock import AsyncMock, patch
from app.recognizer import PlateRecognizer, TURKISH_PLATE_PATTERN


# ---------------------------------------------------------------------------
# Unit Tests — PlateRecognizer (mock _call_litellm)
# ---------------------------------------------------------------------------

class TestRecognizeValidPlate:
    """Mock returns a valid Turkish plate, verify high confidence."""

    @pytest.mark.asyncio
    async def test_recognize_valid_plate(self):
        recognizer = PlateRecognizer(
            litellm_base_url="http://localhost:4000",
            model="glm-ocr",
            api_key="test-key",
        )
        recognizer._call_litellm = AsyncMock(return_value="34 ABC 123")

        result = await recognizer.recognize("fake_base64_image")

        assert result["plate_text"] == "34 ABC 123"
        assert result["confidence"] >= 0.8, (
            f"Expected confidence >= 0.8 for a valid plate, got {result['confidence']}"
        )


class TestRecognizeMalformedPlate:
    """Mock returns garbage text, verify low confidence."""

    @pytest.mark.asyncio
    async def test_recognize_malformed_plate(self):
        recognizer = PlateRecognizer(
            litellm_base_url="http://localhost:4000",
            model="glm-ocr",
            api_key="test-key",
        )
        recognizer._call_litellm = AsyncMock(return_value="XYZGARBAGE")

        result = await recognizer.recognize("fake_base64_image")

        assert result["plate_text"] == "XYZGARBAGE"
        assert result["confidence"] < 0.5, (
            f"Expected confidence < 0.5 for garbage text, got {result['confidence']}"
        )


class TestConfidenceHeuristicKnownPatterns:
    """Multiple valid Turkish formats get high confidence."""

    VALID_PLATES = [
        "06 A 1234",
        "34 ABC 12",
        "35AB1234",
        "01 YZ 999",
        "81BC4567",
        "07 DE 78",
    ]

    MALFORMED_PLATES = [
        "XYZGARBAGE",
        "HELLO",
        "",
        "ABCDEFGH",
    ]

    def setup_method(self):
        self.recognizer = PlateRecognizer(
            litellm_base_url="http://localhost:4000",
            model="glm-ocr",
            api_key="test-key",
        )

    def test_valid_plates_get_high_confidence(self):
        for plate in self.VALID_PLATES:
            confidence = self.recognizer._compute_confidence(plate)
            assert confidence >= 0.8, (
                f"Plate '{plate}' should have confidence >= 0.8, got {confidence}"
            )

    def test_malformed_plates_get_low_confidence(self):
        for plate in self.MALFORMED_PLATES:
            confidence = self.recognizer._compute_confidence(plate)
            assert confidence < 0.5, (
                f"Plate '{plate}' should have confidence < 0.5, got {confidence}"
            )

    def test_partial_match_gets_medium_confidence(self):
        confidence = self.recognizer._compute_confidence("34XXXXXXX")
        assert 0.5 <= confidence < 0.8, (
            f"Partial plate '34XXXXXXX' should have medium confidence, got {confidence}"
        )

    @pytest.mark.asyncio
    async def test_recognize_all_valid_plates_async(self):
        for plate in self.VALID_PLATES:
            self.recognizer._call_litellm = AsyncMock(return_value=plate)
            result = await self.recognizer.recognize("fake_b64")
            assert result["confidence"] >= 0.8, (
                f"Async recognize for '{plate}' should be >= 0.8, got {result['confidence']}"
            )


# ---------------------------------------------------------------------------
# API Tests — FastAPI endpoints (mock module-level recognizer instance)
# ---------------------------------------------------------------------------

@pytest.fixture
def client():
    """Return a synchronous TestClient for the FastAPI app."""
    from fastapi.testclient import TestClient
    from app.main import app
    return TestClient(app)


class TestRecognizeEndpointSuccess:
    """POST /recognize with base64 image, verify response shape."""

    def test_recognize_endpoint_success(self, client):
        fake_result = {"plate_text": "34 ABC 123", "confidence": 0.9, "format_valid": True}

        with patch("app.main.recognizer.recognize", new=AsyncMock(return_value=fake_result)):
            response = client.post(
                "/recognize",
                json={"image": "ZmFrZV9iYXNlNjRfaW1hZ2U="},
            )

        assert response.status_code == 200
        body = response.json()
        assert body["success"] is True
        assert body["plate_text"] == "34 ABC 123"
        assert body["confidence"] == 0.9

    def test_recognize_endpoint_missing_image_field(self, client):
        """Sending no image field should return 422 Unprocessable Entity."""
        response = client.post("/recognize", json={})
        assert response.status_code == 422

    def test_recognize_endpoint_returns_malformed_plate(self, client):
        """Endpoint correctly passes through low-confidence malformed results."""
        fake_result = {"plate_text": "XYZGARBAGE", "confidence": 0.3, "format_valid": False}

        with patch("app.main.recognizer.recognize", new=AsyncMock(return_value=fake_result)):
            response = client.post(
                "/recognize",
                json={"image": "ZmFrZV9iYXNlNjQ="},
            )

        assert response.status_code == 200
        body = response.json()
        assert body["success"] is True
        assert body["confidence"] == 0.3


class TestRecognizeHealth:
    """GET /health returns status."""

    def test_health_returns_status(self, client):
        response = client.get("/health")

        assert response.status_code == 200
        body = response.json()
        assert body["status"] in ("ok", "degraded")
        assert body["service"] == "ocr-recognition"

    def test_health_content_type_is_json(self, client):
        response = client.get("/health")
        assert "application/json" in response.headers["content-type"]
