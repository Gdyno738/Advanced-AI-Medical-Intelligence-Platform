"""
Grad-CAM explainability for the Advanced AI Medical Intelligence Platform.

Automatically selects the correct target layer for each architecture.
"""

import uuid
from pathlib import Path

import cv2
import numpy as np
import torch
from PIL import Image
from torchvision import transforms
from pytorch_grad_cam import GradCAM
from pytorch_grad_cam.utils.image import show_cam_on_image

from app.core.config import IMAGENET_MEAN, IMAGENET_STD, REPORTS_DIR
from app.ml.inference import get_model


def _target_layer(model, architecture: str):
    """Return the last conv layer for Grad-CAM based on architecture."""
    arch = architecture.lower()
    if arch == "densenet121":
        return [model.features.denseblock4.denselayer16.conv2]
    elif arch in ("resnet50", "resnet18"):
        return [model.layer4[-1]]
    elif arch.startswith("efficientnet"):
        return [model.features[-1][0]]
    elif arch == "vgg16":
        return [model.features[-1]]
    elif arch == "mobilenet_v3_small":
        return [model.features[-1][0]]
    else:
        # Generic fallback: last Conv2d found
        last_conv = None
        for m in model.modules():
            if isinstance(m, torch.nn.Conv2d):
                last_conv = m
        if last_conv is None:
            raise ValueError(f"Could not find Conv2d layer for architecture '{architecture}'")
        return [last_conv]


def generate_heatmap(image_path: str, model_id: str = None) -> str:
    """Generate a Grad-CAM heatmap overlay for a medical image.

    Args:
        image_path: Path to the input image.
        model_id:   Registry model ID (defaults to active model).

    Returns:
        Absolute path to the saved heatmap PNG.
    """
    from app.core.model_registry import get_active_model, get_model_by_id

    if model_id:
        entry = get_model_by_id(model_id)
    else:
        entry = get_active_model()

    model, class_names, img_size = get_model(
        entry["id"], entry["model_file"], entry["architecture"]
    )

    path = Path(image_path)
    if not path.exists():
        raise FileNotFoundError(f"Image not found: {image_path}")

    image = Image.open(path).convert("RGB")

    preprocess = transforms.Compose([
        transforms.Resize((img_size, img_size)),
        transforms.ToTensor(),
        transforms.Normalize(mean=IMAGENET_MEAN, std=IMAGENET_STD),
    ])
    to_tensor = transforms.Compose([
        transforms.Resize((img_size, img_size)),
        transforms.ToTensor(),
    ])

    input_tensor = preprocess(image).unsqueeze(0)
    rgb_img = to_tensor(image).permute(1, 2, 0).numpy().astype(np.float32)

    target_layers = _target_layer(model, entry["architecture"])

    with GradCAM(model=model, target_layers=target_layers) as cam:
        grayscale_cam = cam(input_tensor=input_tensor, targets=None)[0]

    cam_image = show_cam_on_image(rgb_img, grayscale_cam, use_rgb=True)

    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    filename = f"gradcam_{uuid.uuid4().hex[:8]}.png"
    output_path = REPORTS_DIR / filename
    cv2.imwrite(str(output_path), cv2.cvtColor(cam_image, cv2.COLOR_RGB2BGR))

    return str(output_path)
