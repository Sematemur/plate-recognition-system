import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient

@pytest.fixture
def mock_detector():
    with patch("app.main.detector") as mock:
        yield mock

@pytest.fixture
def client(mock_detector):
    from app.main import app
    return TestClient(app)
