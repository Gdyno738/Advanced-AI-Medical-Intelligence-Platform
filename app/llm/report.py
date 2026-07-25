"""
LLM-powered medical report generator — Advanced AI Medical Intelligence Platform.

Uses xAI Grok API (OpenAI-compatible) to generate structured clinical reports.
Falls back to a template-based report if the API key is missing or call fails.

Supports all three active analysis modules:
  - Chest X-Ray Pneumonia Detection
  - Brain Tumor MRI Classification
  - Skin Cancer Detection
"""

import os
from app.core.config import XAI_API_KEY, XAI_BASE_URL, GROK_MODEL

# ---------------------------------------------------------------------------
# Per-module prompt templates
# ---------------------------------------------------------------------------

PROMPTS = {
    "NORMAL": (
        "The AI model has classified the chest X-ray as **NORMAL** ({conf:.1f}% confidence). "
        "No significant abnormalities detected in the lung fields."
    ),
    "PNEUMONIA": (
        "The AI model has detected signs consistent with **PNEUMONIA** ({conf:.1f}% confidence) "
        "in the chest X-ray."
    ),
    "glioma": (
        "The AI model has classified the brain MRI as **Glioma** ({conf:.1f}% confidence). "
        "Gliomas are tumors that arise from glial cells in the brain or spine."
    ),
    "meningioma": (
        "The AI model has classified the brain MRI as **Meningioma** ({conf:.1f}% confidence). "
        "Meningiomas arise from the meninges — the membranes surrounding the brain and spinal cord."
    ),
    "notumor": (
        "The AI model has classified the brain MRI as **No Tumor** ({conf:.1f}% confidence). "
        "No evidence of a brain tumor was detected in the MRI scan."
    ),
    "pituitary": (
        "The AI model has classified the brain MRI as showing a **Pituitary Tumor** "
        "({conf:.1f}% confidence). Pituitary tumors develop in the pituitary gland at the base of the brain."
    ),
    "BENIGN": (
        "The AI model has classified the skin lesion as **Benign** ({conf:.1f}% confidence). "
        "No malignant features were detected in the dermoscopy image."
    ),
    "MALIGNANT": (
        "The AI model has classified the skin lesion as **Malignant** ({conf:.1f}% confidence). "
        "Features consistent with malignancy were detected in the dermoscopy image."
    ),
}


# ---------------------------------------------------------------------------
# Grok-powered report
# ---------------------------------------------------------------------------

def _generate_grok_report(predicted_class: str, confidence: float, model_id: str = None) -> str:
    """Generate a clinical report using xAI Grok API."""
    from openai import OpenAI

    client = OpenAI(
        api_key=XAI_API_KEY,
        base_url=XAI_BASE_URL,
    )

    conf_pct = confidence * 100
    finding_hint = PROMPTS.get(predicted_class, f"Classification: {predicted_class}").format(conf=conf_pct)

    # Determine modality context
    modality_ctx = {
        "chest_xray_pneumonia": "chest X-ray",
        "brain_tumor":          "brain MRI",
        "skin_cancer":          "dermoscopy image",
    }.get(model_id or "", "medical image")

    prompt = (
        f"You are a senior radiologist AI assistant generating a structured medical analysis report.\n\n"
        f"Image type: {modality_ctx}\n"
        f"AI Finding: {finding_hint}\n\n"
        f"Write a professional clinical report using markdown with these sections:\n"
        f"## Medical Analysis Report\n"
        f"**Classification** and **Confidence** (one line each)\n"
        f"### Clinical Findings\n"
        f"2-3 sentences explaining what this classification means clinically.\n"
        f"### Grad-CAM Interpretation\n"
        f"1-2 sentences on how to interpret the attention heatmap.\n"
        f"### Recommendation\n"
        f"Appropriate next steps based on the finding.\n\n"

        f"Keep tone professional, concise, and accessible to both clinicians and patients."
    )

    response = client.chat.completions.create(
        model=GROK_MODEL,
        messages=[
            {"role": "system", "content": "You are a professional medical AI report generator."},
            {"role": "user",   "content": prompt},
        ],
        temperature=0.25,
        max_tokens=900,
    )

    report = response.choices[0].message.content.strip()

    return report


# ---------------------------------------------------------------------------
# Fallback template report
# ---------------------------------------------------------------------------

def _generate_template_report(predicted_class: str, confidence: float, model_id: str = None) -> str:
    """Template-based fallback when no API key is available."""
    conf_pct = confidence * 100
    finding = PROMPTS.get(predicted_class, f"Classification: **{predicted_class}**").format(conf=conf_pct)

    modality = {
        "chest_xray_pneumonia": "Chest X-Ray",
        "brain_tumor":          "Brain MRI",
        "skin_cancer":          "Skin Dermoscopy",
    }.get(model_id or "", "Medical Image")

    rec = (
        "Immediate medical evaluation is strongly recommended."
        if predicted_class in ("PNEUMONIA", "MALIGNANT", "glioma", "meningioma", "pituitary")
        else "Routine clinical follow-up as indicated."
    )

    return (
        f"## {modality} Analysis Report\n\n"
        f"**Classification:** {predicted_class}  \n"
        f"**Confidence:** {conf_pct:.1f}%\n\n"
        f"### Clinical Findings\n\n"
        f"{finding}\n\n"
        f"### Grad-CAM Interpretation\n\n"
        f"The Grad-CAM heatmap highlights the image regions most influential "
        f"in the AI model's decision. Areas with warm colours (red/yellow) "
        f"indicate the regions the model weighted most heavily.\n\n"
        f"### Recommendation\n\n"
        f"{rec}\n"
    )


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def generate_report(
    predicted_class: str,
    confidence: float,
    model_id: str = None,
) -> str:
    """Generate a medical analysis report.

    Uses xAI Grok if XAI_API_KEY is configured, otherwise falls back to
    a structured template report.

    Args:
        predicted_class: The model's predicted class label.
        confidence:      Confidence score (0–1).
        model_id:        Registry model ID for context-aware prompting.

    Returns:
        Formatted markdown report string.
    """
    if XAI_API_KEY:
        try:
            return _generate_grok_report(predicted_class, confidence, model_id)
        except Exception as exc:
            print(f"[WARNING] Grok API call failed, using template report: {exc}")
    return _generate_template_report(predicted_class, confidence, model_id)
