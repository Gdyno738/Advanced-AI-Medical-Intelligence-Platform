"""
Multi-model inference engine for the Advanced AI Medical Intelligence Platform.

Each model is loaded lazily on first use and cached in memory.
Supports any architecture registered in the model registry.

Supported architectures:
  densenet121   — DenseNet-121 (chest X-ray pneumonia)
  efficientnet_b3 — EfficientNet-B3 (skin lesion)
  resnet50      — ResNet-50 (brain tumor)
  resnet18      — ResNet-18 (generic)
  vgg16         — VGG-16 (generic)
"""

import os
import torch
import torch.nn.functional as F
from torchvision import models, transforms

# DevOps Memory Optimization: Limit threads to prevent OOM kills on PaaS Free Tiers
torch.set_num_threads(2)
from PIL import Image
from pathlib import Path
from typing import Optional

from app.core.config import MODEL_DIR, IMAGENET_MEAN, IMAGENET_STD

_device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

# Cache: model_id -> (model, class_names)
_model_cache: dict = {}


# ---------------------------------------------------------------------------
# Architecture builders
# ---------------------------------------------------------------------------

def _build_model(architecture: str, num_classes: int):
    """Instantiate a model architecture with the correct classifier head."""
    arch = architecture.lower()

    if arch == "densenet121":
        m = models.densenet121(weights=None)
        m.classifier = torch.nn.Linear(m.classifier.in_features, num_classes)

    elif arch in ("efficientnet_b0", "efficientnet_b3", "efficientnet_b4"):
        builder = getattr(models, arch)
        m = builder(weights=None)
        m.classifier[-1] = torch.nn.Linear(m.classifier[-1].in_features, num_classes)

    elif arch == "resnet50":
        m = models.resnet50(weights=None)
        m.fc = torch.nn.Linear(m.fc.in_features, num_classes)

    elif arch == "resnet18":
        m = models.resnet18(weights=None)
        m.fc = torch.nn.Linear(m.fc.in_features, num_classes)

    elif arch == "vgg16":
        m = models.vgg16(weights=None)
        m.classifier[-1] = torch.nn.Linear(m.classifier[-1].in_features, num_classes)

    elif arch == "mobilenet_v3_small":
        m = models.mobilenet_v3_small(weights=None)
        m.classifier[-1] = torch.nn.Linear(m.classifier[-1].in_features, num_classes)

    else:
        raise ValueError(
            f"Unknown architecture '{architecture}'. "
            "Add it to inference.py _build_model()."
        )

    return m


# ---------------------------------------------------------------------------
# Loader
# ---------------------------------------------------------------------------

def _load(model_id: str, model_file: str, architecture: str) -> tuple:
    """Load and cache a model from the models/ directory."""
    path = MODEL_DIR / model_file
    if not path.exists():
        raise FileNotFoundError(
            f"Model file not found: {path}. "
            "Place the checkpoint in the models/ directory."
        )

    checkpoint = torch.load(path, map_location=_device, weights_only=False)

    # Support both wrapped checkpoints and raw state dicts
    if isinstance(checkpoint, dict) and "model_state_dict" in checkpoint:
        class_names = checkpoint.get("class_names", ["NORMAL", "PNEUMONIA"])
        state_dict  = checkpoint["model_state_dict"]
        arch        = checkpoint.get("architecture", architecture)
        img_size    = checkpoint.get("img_size", 224)
    else:
        # Raw state dict — use registry values
        raise ValueError(
            f"Checkpoint '{model_file}' is a raw state dict without metadata. "
            "Run tools/convert_checkpoint.py to wrap it first."
        )

    model = _build_model(arch, len(class_names))
    model.load_state_dict(state_dict)
    model.to(_device)
    model.eval()

    return model, class_names, img_size


def get_model(model_id: str, model_file: str, architecture: str):
    """Return (model, class_names, img_size) — loads on first call, cached after."""
    if model_id not in _model_cache:
        _model_cache[model_id] = _load(model_id, model_file, architecture)
    return _model_cache[model_id]


# ---------------------------------------------------------------------------
# Public inference API
# ---------------------------------------------------------------------------

def predict(image_path: str, model_id: Optional[str] = None) -> dict:
    """Run inference using the specified model (or active model if None).

    Args:
        image_path: Path to the input image.
        model_id:   Registry model ID. Defaults to the active model.

    Returns:
        dict: predicted_class, confidence, probabilities {class: prob}.
    """
    from app.core.model_registry import get_active_model, get_model_by_id

    if model_id:
        registry_entry = get_model_by_id(model_id)
        if registry_entry is None:
            raise ValueError(f"Unknown model_id: {model_id}")
    else:
        registry_entry = get_active_model()

    model, class_names, img_size = get_model(
        registry_entry["id"],
        registry_entry["model_file"],
        registry_entry["architecture"],
    )

    path = Path(image_path)
    if not path.exists():
        raise FileNotFoundError(f"Image not found: {image_path}")

    try:
        image = Image.open(path).convert("RGB")
    except Exception as exc:
        raise ValueError(f"Cannot open image: {exc}") from exc

    preprocess = transforms.Compose([
        transforms.Resize((img_size, img_size)),
        transforms.ToTensor(),
        transforms.Normalize(mean=IMAGENET_MEAN, std=IMAGENET_STD),
    ])

    input_tensor = preprocess(image).unsqueeze(0).to(_device)

    with torch.no_grad():
        probs = F.softmax(model(input_tensor), dim=1)[0]
        predicted_idx = int(torch.argmax(probs).item())

    prob_map = {
        class_names[i]: round(float(probs[i].item()), 4)
        for i in range(len(class_names))
    }

    return {
        "predicted_class": class_names[predicted_idx],
        "confidence":      prob_map[class_names[predicted_idx]],
        "probabilities":   prob_map,
    }
