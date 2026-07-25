"""
Utility script to create a test model checkpoint.

Generates a DenseNet121 with random (untrained) weights and saves it in
the same checkpoint format the application expects. This is for testing
and development only — replace with a properly trained model for production.

Usage:
    python tests/create_test_model.py
"""

import sys
from pathlib import Path

# Ensure the project root is on sys.path so imports work
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

import torch
from torchvision import models


def create_test_checkpoint(output_path: str | None = None) -> Path:
    """Create a DenseNet121 checkpoint with random weights.

    Args:
        output_path: Where to save the checkpoint. Defaults to models/model.pt.

    Returns:
        Path to the saved checkpoint file.
    """
    from app.core.config import MODEL_PATH, MODEL_DIR

    save_path = Path(output_path) if output_path else MODEL_PATH
    save_path.parent.mkdir(parents=True, exist_ok=True)

    # Build DenseNet121 with random weights
    model = models.densenet121(weights=None)
    num_classes = 2
    in_features = model.classifier.in_features
    model.classifier = torch.nn.Linear(in_features, num_classes)

    checkpoint = {
        "model_state_dict": model.state_dict(),
        "class_names": ["NORMAL", "PNEUMONIA"],
        "architecture": "densenet121",
        "img_size": 224,
    }

    torch.save(checkpoint, save_path)
    print(f"[OK] Test checkpoint saved to {save_path} ({save_path.stat().st_size / 1e6:.1f} MB)")
    return save_path


if __name__ == "__main__":
    create_test_checkpoint()
