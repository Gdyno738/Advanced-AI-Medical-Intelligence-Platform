"""
Tests for the inference module.

Verifies that predict() loads the model, processes an image, and returns
results with the expected structure and value ranges.
"""

import sys
from pathlib import Path

import pytest
import numpy as np
from PIL import Image

# Ensure project root is on sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from app.core.config import MODEL_PATH, IMG_SIZE


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(scope="session", autouse=True)
def ensure_test_model():
    """Create a test model checkpoint if one doesn't already exist."""
    if not MODEL_PATH.exists():
        from tests.create_test_model import create_test_checkpoint
        create_test_checkpoint()


@pytest.fixture
def sample_image_path(tmp_path: Path) -> str:
    """Create a synthetic RGB image for testing."""
    img_array = np.random.randint(0, 255, (IMG_SIZE, IMG_SIZE, 3), dtype=np.uint8)
    img = Image.fromarray(img_array, "RGB")
    img_path = tmp_path / "test_xray.png"
    img.save(img_path)
    return str(img_path)


@pytest.fixture
def corrupt_file(tmp_path: Path) -> str:
    """Create a corrupt (non-image) file for error handling tests."""
    bad_path = tmp_path / "corrupt.png"
    bad_path.write_text("this is not an image")
    return str(bad_path)


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestPredict:
    """Tests for the predict() function."""

    def test_returns_expected_keys(self, sample_image_path: str):
        """predict() should return a dict with 'predicted_class' and 'confidence'."""
        from app.ml.inference import predict

        result = predict(sample_image_path)
        assert isinstance(result, dict)
        assert "predicted_class" in result
        assert "confidence" in result

    def test_predicted_class_is_valid(self, sample_image_path: str):
        """The predicted class should be one of the known class names."""
        from app.ml.inference import predict

        result = predict(sample_image_path)
        assert result["predicted_class"] in ["NORMAL", "PNEUMONIA"]

    def test_confidence_in_valid_range(self, sample_image_path: str):
        """Confidence score should be between 0 and 1."""
        from app.ml.inference import predict

        result = predict(sample_image_path)
        assert 0.0 <= result["confidence"] <= 1.0

    def test_confidence_is_float(self, sample_image_path: str):
        """Confidence should be a Python float."""
        from app.ml.inference import predict

        result = predict(sample_image_path)
        assert isinstance(result["confidence"], float)

    def test_missing_image_raises_file_not_found(self):
        """predict() should raise FileNotFoundError for a nonexistent path."""
        from app.ml.inference import predict

        with pytest.raises(FileNotFoundError):
            predict("/nonexistent/path/to/image.png")

    def test_corrupt_image_raises_value_error(self, corrupt_file: str):
        """predict() should raise ValueError for a corrupt/non-image file."""
        from app.ml.inference import predict

        with pytest.raises(ValueError):
            predict(corrupt_file)
