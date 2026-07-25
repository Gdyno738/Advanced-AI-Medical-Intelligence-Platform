"""
One-time conversion utility: wrap an existing checkpoint into the format
expected by the Medical AI Platform inference module.

Usage:
    python tools/convert_checkpoint.py --input path/to/your/checkpoint.pth

The script auto-detects whether the input is:
  (a) A raw state_dict  (saved with torch.save(model.state_dict(), ...))
  (b) A dict that already has model_state_dict / state_dict key
  (c) Already in the correct app format (just copies it)

Output: models/model.pt  (ready to use immediately)
"""

import sys
import argparse
from pathlib import Path

# Make sure project root is importable
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

import torch
from torchvision import models


def wrap_checkpoint(input_path: str, output_path: str | None = None) -> Path:
    """Convert any DenseNet121 checkpoint into the app's expected format.

    Args:
        input_path: Path to your existing checkpoint file.
        output_path: Where to save the converted file.
                     Defaults to models/model.pt.

    Returns:
        Path to the saved output file.
    """
    from app.core.config import MODEL_PATH

    src = Path(input_path)
    if not src.exists():
        raise FileNotFoundError(f"Input checkpoint not found: {src}")

    dst = Path(output_path) if output_path else MODEL_PATH
    dst.parent.mkdir(parents=True, exist_ok=True)

    print(f"Loading checkpoint from: {src}")
    raw = torch.load(src, map_location="cpu", weights_only=False)

    # --- Detect checkpoint type ---
    if isinstance(raw, dict):
        keys = set(raw.keys())

        # Already in correct format
        if "model_state_dict" in keys and "class_names" in keys:
            print("[INFO] Checkpoint already in correct format — copying as-is.")
            checkpoint = raw

        # Has state_dict key (common Pytorch Lightning / manual save pattern)
        elif "state_dict" in keys:
            print("[INFO] Found 'state_dict' key — wrapping.")
            checkpoint = {
                "model_state_dict": raw["state_dict"],
                "class_names": raw.get("class_names", ["NORMAL", "PNEUMONIA"]),
                "architecture": "densenet121",
                "img_size": raw.get("img_size", 224),
            }

        # Looks like a raw state_dict (all keys are layer names)
        elif all("." in k for k in list(keys)[:5]):
            print("[INFO] Detected raw state_dict — wrapping.")
            checkpoint = {
                "model_state_dict": raw,
                "class_names": ["NORMAL", "PNEUMONIA"],
                "architecture": "densenet121",
                "img_size": 224,
            }

        else:
            print(f"[WARNING] Unknown dict keys: {list(keys)[:10]}")
            print("Attempting to use as raw state_dict...")
            checkpoint = {
                "model_state_dict": raw,
                "class_names": ["NORMAL", "PNEUMONIA"],
                "architecture": "densenet121",
                "img_size": 224,
            }

    else:
        raise ValueError(
            f"Unexpected checkpoint type: {type(raw)}. "
            "Expected a dict (state_dict or full checkpoint)."
        )

    # --- Validate the state_dict loads into DenseNet121 ---
    print("Validating state_dict against DenseNet121 architecture...")
    num_classes = len(checkpoint["class_names"])
    test_model = models.densenet121(weights=None)
    test_model.classifier = torch.nn.Linear(
        test_model.classifier.in_features, num_classes
    )
    try:
        test_model.load_state_dict(checkpoint["model_state_dict"], strict=True)
        print(f"[OK] State dict validated — {num_classes} classes: {checkpoint['class_names']}")
    except RuntimeError as e:
        print(f"[ERROR] State dict does not match DenseNet121: {e}")
        print("Common causes:")
        print("  - Model has a different classifier head size")
        print("  - Model is a different architecture")
        print("  - Keys have a prefix (e.g. 'model.features.') from Lightning")
        print("\nTry stripping key prefix and re-running, or contact support.")
        sys.exit(1)

    # --- Save ---
    torch.save(checkpoint, dst)
    size_mb = dst.stat().st_size / 1e6
    print(f"[OK] Saved to {dst} ({size_mb:.1f} MB)")
    print(f"\nRestart the backend to pick up the new model:")
    print(f"  uvicorn app.api.main:app --reload --port 8000")
    return dst


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Convert a DenseNet121 checkpoint to app format")
    parser.add_argument("--input", required=True, help="Path to your existing checkpoint file")
    parser.add_argument("--output", default=None, help="Output path (default: models/model.pt)")
    args = parser.parse_args()

    wrap_checkpoint(args.input, args.output)
