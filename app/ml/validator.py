"""
Task-aware input validation for the Medical AI Platform.

Reads validation rules from the Model Registry so each model type can
define its own acceptance criteria — chest X-rays require grayscale,
dermoscopy images may allow colour, MRI scans need minimum resolution, etc.

For any model not in the registry, sensible defaults are applied.
"""

import numpy as np
from PIL import Image
from pathlib import Path


# ---------------------------------------------------------------------------
# Default rules (used when no registry entry specifies otherwise)
# ---------------------------------------------------------------------------

DEFAULT_RULES = {
    "require_grayscale":    True,
    "max_mean_brightness":  185,
    "min_dimension":        100,
}


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def validate_medical_image(image_path: str, validation_rules: dict | None = None) -> dict:
    """Validate that an uploaded image is suitable for the active model.

    Args:
        image_path:        Absolute path to the saved upload.
        validation_rules:  Dict from the registry entry's "validation" key.
                           Falls back to DEFAULT_RULES if None.

    Returns:
        dict with:
            is_valid   (bool)   — True = accept, False = reject.
            reason     (str)    — Human-readable rejection reason (None if valid).
            color_std  (float)  — Measured colour deviation.
            brightness (float)  — Measured mean brightness.
    """
    rules = {**DEFAULT_RULES, **(validation_rules or {})}
    path  = Path(image_path)

    try:
        img = Image.open(path).convert("RGB")
    except Exception:
        return {
            "is_valid":   False,
            "reason":     "Could not open the uploaded file as an image.",
            "color_std":  0.0,
            "brightness": 0.0,
        }

    w, h  = img.size
    arr   = np.array(img, dtype=np.float32)       # (H, W, 3)
    r, g, b = arr[:, :, 0], arr[:, :, 1], arr[:, :, 2]

    # Colour deviation score
    color_std  = float((np.std(r - g) + np.std(r - b) + np.std(g - b)) / 3.0)
    brightness = float(arr.mean())

    # ── Size check (applies to all models) ───────────────────────────────
    min_dim = int(rules.get("min_dimension", 100))
    if w < min_dim or h < min_dim:
        return {
            "is_valid":   False,
            "reason":     (
                f"Image is too small ({w}×{h} px). "
                f"Please upload a full-resolution medical image (minimum {min_dim}×{min_dim} px)."
            ),
            "color_std":  color_std,
            "brightness": brightness,
        }

    # ── Grayscale check (only for models that require it) ────────────────
    if rules.get("require_grayscale", True):
        threshold = 18.0
        if color_std > threshold:
            return {
                "is_valid":   False,
                "reason":     (
                    "This appears to be a colour photograph, not a medical image. "
                    "The expected input for this analysis module is a grayscale scan "
                    "(e.g. chest X-ray, MRI). Please upload a valid medical image."
                ),
                "color_std":  color_std,
                "brightness": brightness,
            }

    # ── Brightness check ─────────────────────────────────────────────────
    max_brightness = float(rules.get("max_mean_brightness", 185))
    if brightness > max_brightness:
        return {
            "is_valid":   False,
            "reason":     (
                "This image is too bright to be a medical scan. "
                "Medical images are typically dark. Please upload a valid scan."
            ),
            "color_std":  color_std,
            "brightness": brightness,
        }

    return {
        "is_valid":   True,
        "reason":     None,
        "color_std":  color_std,
        "brightness": brightness,
    }


# ---------------------------------------------------------------------------
# Backwards-compatible alias (used by main.py)
# ---------------------------------------------------------------------------

def validate_xray_image(image_path: str) -> dict:
    """Validate using the active model's rules from the registry."""
    try:
        from app.core.model_registry import get_active_model
        active = get_active_model()
        rules  = active.get("validation", DEFAULT_RULES)
    except Exception:
        rules = DEFAULT_RULES

    return validate_medical_image(image_path, rules)
