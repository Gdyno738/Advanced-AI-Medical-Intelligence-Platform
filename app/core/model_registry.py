"""
Model Registry — Advanced AI Medical Intelligence Platform.

Three active models:
  1. Chest X-Ray Pneumonia Detection  (DenseNet121 · NORMAL / PNEUMONIA)
  2. Brain Tumor Classification        (DenseNet121 · glioma / meningioma / notumor / pituitary)
  3. Skin Cancer Detection             (DenseNet121 · BENIGN / MALIGNANT)
"""

from app.core.config import MODEL_DIR

MODEL_REGISTRY: dict = {

    # ── 1. Chest X-Ray Pneumonia ─────────────────────────────────────────
    "chest_xray_pneumonia": {
        "id":          "chest_xray_pneumonia",
        "name":        "Chest X-Ray Pneumonia Detector",
        "description": "Detects pneumonia from chest X-ray images using DenseNet121 trained on the Kaggle Chest X-Ray dataset (5,863 images).",
        "version":     "1.0.0",
        "task":        "binary_classification",
        "input_type":  "chest_xray",
        "classes":     ["NORMAL", "PNEUMONIA"],
        "organ":       "Lungs",
        "modality":    "X-Ray",
        "architecture":"densenet121",
        "img_size":    224,
        "model_file":  "model.pt",
        "validation": {
            "require_grayscale":   True,
            "max_mean_brightness": 185,
            "min_dimension":       100,
        },
        "active": True,
        "tags":   ["pneumonia", "chest", "x-ray", "DenseNet"],
    },

    # ── 2. Brain Tumor ───────────────────────────────────────────────────
    "brain_tumor": {
        "id":          "brain_tumor",
        "name":        "Brain Tumor MRI Classifier",
        "description": "Classifies brain MRI scans into 4 tumor categories using DenseNet121 trained on the Kaggle Brain Tumor dataset (3,264 images).",
        "version":     "1.0.0",
        "task":        "multiclass_classification",
        "input_type":  "brain_mri",
        "classes":     ["glioma", "meningioma", "notumor", "pituitary"],
        "organ":       "Brain",
        "modality":    "MRI",
        "architecture":"densenet121",
        "img_size":    224,
        "model_file":  "brain_tumor_model.pt",
        "validation": {
            "require_grayscale":   True,
            "max_mean_brightness": 200,
            "min_dimension":       100,
        },
        "active": True,
        "tags":   ["brain", "tumor", "MRI", "glioma", "meningioma", "DenseNet"],
    },

    # ── 3. Skin Cancer ───────────────────────────────────────────────────
    "skin_cancer": {
        "id":          "skin_cancer",
        "name":        "Skin Cancer Detector",
        "description": "Classifies dermoscopy images as benign or malignant using DenseNet121 trained on the ISIC Skin Cancer dataset.",
        "version":     "1.0.0",
        "task":        "binary_classification",
        "input_type":  "dermoscopy",
        "classes":     ["BENIGN", "MALIGNANT"],
        "organ":       "Skin",
        "modality":    "Dermoscopy",
        "architecture":"densenet121",
        "img_size":    224,
        "model_file":  "skin_cancer_model.pt",
        "validation": {
            "require_grayscale":   False,   # dermoscopy = colour images
            "max_mean_brightness": 230,
            "min_dimension":       100,
        },
        "active": True,
        "tags":   ["skin", "cancer", "dermoscopy", "ISIC", "DenseNet"],
    },
}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def get_active_model(model_id: str = None) -> dict:
    """Return model entry by ID, or the first available active model."""
    if model_id and model_id in MODEL_REGISTRY:
        entry = MODEL_REGISTRY[model_id]
        if (MODEL_DIR / entry["model_file"]).exists():
            return entry
        raise RuntimeError(f"Model file missing for '{model_id}': {entry['model_file']}")

    for entry in MODEL_REGISTRY.values():
        if entry.get("active") and (MODEL_DIR / entry["model_file"]).exists():
            return entry
    raise RuntimeError("No active model found. Check models/ directory.")


def get_all_models() -> list:
    result = []
    for entry in MODEL_REGISTRY.values():
        info = dict(entry)
        info["model_available"] = (MODEL_DIR / entry["model_file"]).exists()
        result.append(info)
    return result


def get_model_by_id(model_id: str) -> dict | None:
    return MODEL_REGISTRY.get(model_id)
