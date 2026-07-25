"""
Tests for the FastAPI API endpoints.

Verifies that /predict, /history, /health return correct status codes
and response shapes using FastAPI's TestClient.
"""

import sys
from pathlib import Path
from io import BytesIO

import pytest
import numpy as np
from PIL import Image

# Ensure project root is on sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(scope="session", autouse=True)
def ensure_test_model():
    """Create a test model checkpoint if one doesn't already exist."""
    from app.core.config import MODEL_PATH
    if not MODEL_PATH.exists():
        from tests.create_test_model import create_test_checkpoint
        create_test_checkpoint()


@pytest.fixture(scope="module")
def client():
    """Create a FastAPI TestClient for the API."""
    from fastapi.testclient import TestClient
    from app.api.main import app
    with TestClient(app) as c:
        yield c


@pytest.fixture
def sample_image_bytes() -> bytes:
    """Create a synthetic chest X-ray image as bytes."""
    img_array = np.random.randint(0, 255, (224, 224, 3), dtype=np.uint8)
    img = Image.fromarray(img_array, "RGB")
    buffer = BytesIO()
    img.save(buffer, format="PNG")
    buffer.seek(0)
    return buffer.getvalue()


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestHealthEndpoint:
    """Tests for GET /health."""

    def test_health_returns_200(self, client):
        """Health endpoint should return 200 OK."""
        response = client.get("/health")
        assert response.status_code == 200

    def test_health_response_shape(self, client):
        """Health response should have a 'status' key."""
        response = client.get("/health")
        data = response.json()
        assert "status" in data
        assert data["status"] == "healthy"


class TestPredictEndpoint:
    """Tests for POST /predict."""

    def test_predict_returns_200(self, client, sample_image_bytes):
        """Predict endpoint should return 200 with a valid image."""
        response = client.post(
            "/predict",
            files={"file": ("test_xray.png", sample_image_bytes, "image/png")},
        )
        assert response.status_code == 200

    def test_predict_response_shape(self, client, sample_image_bytes):
        """Predict response should contain all expected fields."""
        response = client.post(
            "/predict",
            files={"file": ("test_xray.png", sample_image_bytes, "image/png")},
        )
        data = response.json()
        assert "id" in data
        assert "predicted_class" in data
        assert "confidence" in data
        assert "report_text" in data
        assert "heatmap_path" in data
        assert "created_at" in data

    def test_predict_class_is_valid(self, client, sample_image_bytes):
        """Predicted class should be one of the known labels."""
        response = client.post(
            "/predict",
            files={"file": ("test_xray.png", sample_image_bytes, "image/png")},
        )
        data = response.json()
        assert data["predicted_class"] in ["NORMAL", "PNEUMONIA"]

    def test_predict_confidence_range(self, client, sample_image_bytes):
        """Confidence should be between 0 and 1."""
        response = client.post(
            "/predict",
            files={"file": ("test_xray.png", sample_image_bytes, "image/png")},
        )
        data = response.json()
        assert 0.0 <= data["confidence"] <= 1.0


class TestHistoryEndpoints:
    """Tests for GET /history and GET /history/{id}."""

    def test_history_returns_200(self, client):
        """History list endpoint should return 200."""
        response = client.get("/history")
        assert response.status_code == 200

    def test_history_returns_list(self, client):
        """History response should be a list."""
        response = client.get("/history")
        data = response.json()
        assert isinstance(data, list)

    def test_history_detail_after_prediction(self, client, sample_image_bytes):
        """After creating a prediction, its detail should be retrievable."""
        # Create a prediction first
        create_resp = client.post(
            "/predict",
            files={"file": ("test_xray.png", sample_image_bytes, "image/png")},
        )
        prediction_id = create_resp.json()["id"]

        # Fetch its detail
        detail_resp = client.get(f"/history/{prediction_id}")
        assert detail_resp.status_code == 200
        data = detail_resp.json()
        assert data["id"] == prediction_id
        assert "report_text" in data
        assert "heatmap_path" in data

    def test_history_detail_not_found(self, client):
        """Requesting a non-existent prediction should return 404."""
        response = client.get("/history/999999")
        assert response.status_code == 404
