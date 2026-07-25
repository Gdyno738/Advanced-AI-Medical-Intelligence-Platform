"""
Pydantic schemas for the Medical AI Platform REST API.

Defines the data shapes used in API endpoints for validation,
serialization, and auto-generated OpenAPI documentation.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field


# ---------------------------------------------------------------------------
# Model Registry Schemas
# ---------------------------------------------------------------------------

class ModelModuleInfo(BaseModel):
    """Describes one registered AI analysis module."""
    id:              str
    name:            str
    description:     str
    version:         str
    task:            str
    input_type:      str
    classes:         List[str]
    organ:           str
    modality:        str
    architecture:    str
    img_size:        int
    active:          bool
    model_available: bool
    tags:            List[str]


# ---------------------------------------------------------------------------
# Health & System Schemas
# ---------------------------------------------------------------------------

class ActiveModelSummary(BaseModel):
    """Compact summary of the currently loaded model."""
    id:           str
    name:         str
    architecture: str
    classes:      List[str]
    task:         str
    modality:     str
    organ:        str


class HealthResponse(BaseModel):
    """Response model for GET /health."""
    status:       str  = Field("healthy", description="Service health status")
    active_model: Optional[ActiveModelSummary] = Field(
        None, description="Currently loaded AI model summary"
    )


# ---------------------------------------------------------------------------
# Prediction Schemas
# ---------------------------------------------------------------------------

class PredictionResponse(BaseModel):
    """Full response for POST /predict."""

    id:             int   = Field(..., description="Database ID of the prediction record")
    image_filename: str   = Field(..., description="Original uploaded filename")
    predicted_class:str   = Field(..., description="Top predicted class label")
    confidence:     float = Field(..., ge=0.0, le=1.0, description="Top-class confidence score")
    probabilities:  Optional[Dict[str, float]] = Field(
        None, description="Full probability distribution across all classes"
    )
    report_text:    Optional[str]  = Field(None, description="LLM-generated medical report")
    heatmap_path:   Optional[str]  = Field(None, description="Path to the Grad-CAM heatmap image")
    warning:        Optional[str]  = Field(None, description="Warning if image may not be a valid medical scan")
    model_id:       Optional[str]  = Field(None, description="Registry ID of the model used")
    created_at:     datetime       = Field(..., description="Timestamp of the prediction (UTC)")

    model_config = ConfigDict(from_attributes=True)


class PredictionHistoryItem(BaseModel):
    """Compact row for GET /history list."""

    id:             int
    image_filename: str
    predicted_class:str
    confidence:     float
    created_at:     datetime

    model_config = ConfigDict(from_attributes=True)


class PredictionDetail(BaseModel):
    """Full detail for GET /history/{id}."""

    id:             int
    image_filename: str
    predicted_class:str
    confidence:     float
    probabilities:  Optional[Dict[str, float]] = None
    report_text:    Optional[str]  = None
    heatmap_path:   Optional[str]  = None
    warning:        Optional[str]  = None
    model_id:       Optional[str]  = None
    created_at:     datetime

    model_config = ConfigDict(from_attributes=True)
