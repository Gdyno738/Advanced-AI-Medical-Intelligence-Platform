"""
FastAPI application — REST API for the Medical AI Platform.

Endpoints:
  GET  /health            — service healthcheck + active model info
  GET  /models            — list all registered AI analysis modules
  POST /predict           — upload a medical image → full analysis pipeline
  GET  /history           — list past predictions
  GET  /history/{id}      — full details for a specific prediction

Auto-generated Swagger docs at /docs.
"""

import json
import shutil
import uuid
from contextlib import asynccontextmanager
from pathlib import Path
from typing import List

from fastapi import FastAPI, UploadFile, File, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.core.config import REPORTS_DIR, UPLOAD_DIR
from app.core.model_registry import get_active_model, get_all_models
from app.db.session import init_db, get_db
from app.db.models import Prediction
from app.ml.inference import predict
from app.ml.gradcam import generate_heatmap
from app.llm.report import generate_report
from app.ml.validator import validate_medical_image
from app.api.schemas import (
    PredictionResponse,
    PredictionHistoryItem,
    PredictionDetail,
    HealthResponse,
    ActiveModelSummary,
    ModelModuleInfo,
)

# ---------------------------------------------------------------------------
# Lifespan
# ---------------------------------------------------------------------------

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize DB and required directories on startup."""
    init_db()
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    yield


# ---------------------------------------------------------------------------
# App setup
# ---------------------------------------------------------------------------

app = FastAPI(
    title="Advanced AI Medical Intelligence Platform",
    description=(
        "An extensible AI platform for medical image analysis. "
        "Analyze medical images, predict diseases using Deep Learning (DenseNet121), "
        "explain predictions with Grad-CAM XAI, and generate AI-assisted clinical reports via LLM. "
        "Designed to support multiple imaging modalities: X-Ray, MRI, CT, Dermoscopy, Fundus."
    ),
    version="1.0.0",
    lifespan=lifespan,
    contact={"name": "Medical AI Platform"},
    license_info={"name": "MIT"},
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

REPORTS_DIR.mkdir(parents=True, exist_ok=True)
app.mount("/reports", StaticFiles(directory=str(REPORTS_DIR)), name="reports")


# ---------------------------------------------------------------------------
# System Endpoints
# ---------------------------------------------------------------------------

@app.get(
    "/health",
    response_model=HealthResponse,
    tags=["System"],
    summary="Service health check",
    description="Returns service status and the currently active AI model summary.",
)
def health_check():
    """Return service health status and active model metadata."""
    try:
        active = get_active_model()
        model_summary = ActiveModelSummary(
            id=active["id"],
            name=active["name"],
            architecture=active["architecture"],
            classes=active["classes"],
            task=active["task"],
            modality=active["modality"],
            organ=active["organ"],
        )
    except Exception:
        model_summary = None

    return HealthResponse(status="healthy", active_model=model_summary)


@app.get(
    "/models",
    response_model=List[ModelModuleInfo],
    tags=["System"],
    summary="List all registered AI analysis modules",
    description=(
        "Returns the full model registry — all registered analysis modules, "
        "their tasks, supported image types, classes, and availability status."
    ),
)
def list_models():
    """List every model registered in the platform registry."""
    entries = get_all_models()
    return [
        ModelModuleInfo(
            id=e["id"],
            name=e["name"],
            description=e["description"],
            version=e["version"],
            task=e["task"],
            input_type=e["input_type"],
            classes=e["classes"],
            organ=e["organ"],
            modality=e["modality"],
            architecture=e["architecture"],
            img_size=e["img_size"],
            active=e["active"],
            model_available=e["model_available"],
            tags=e.get("tags", []),
        )
        for e in entries
    ]


# ---------------------------------------------------------------------------
# Prediction Endpoint
# ---------------------------------------------------------------------------

@app.post(
    "/predict",
    response_model=PredictionResponse,
    tags=["Predictions"],
    summary="Analyze a medical image",
    description=(
        "Upload a medical image and receive a full AI analysis. "
        "Optionally pass ?model_id= to select a specific analysis module "
        "(chest_xray_pneumonia | brain_tumor | skin_cancer). "
        "Defaults to the first available active model."
    ),
)
def create_prediction(
    file: UploadFile = File(..., description="Medical image file (JPEG/PNG/BMP/TIFF)"),
    model_id: str = None,
    db: Session = Depends(get_db),
):
    """
    Full analysis pipeline:
    1. Save uploaded image
    2. Validate image suitability for the active model
    3. Run DenseNet121 inference → class probabilities
    4. Generate Grad-CAM attention heatmap
    5. Generate LLM clinical report
    6. Persist everything to the database
    """
    # Resolve model from registry (use requested model_id or first active)
    try:
        active_model = get_active_model(model_id)
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc))
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    # 1. Save uploaded file
    file_ext = Path(file.filename).suffix or ".png"
    saved_filename = f"{uuid.uuid4().hex}{file_ext}"
    saved_path = UPLOAD_DIR / saved_filename

    try:
        with open(saved_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Failed to save uploaded file: {exc}")

    # 2. Validate using the SELECTED model's validation rules
    validation = validate_medical_image(
        str(saved_path),
        active_model.get("validation")
    )
    if not validation["is_valid"]:
        saved_path.unlink(missing_ok=True)
        raise HTTPException(
            status_code=422,
            detail={
                "error":   "invalid_image",
                "message": validation["reason"],
                "hint": (
                    f"This module expects a {active_model['modality']} image "
                    f"of the {active_model['organ']}. "
                    "Please upload a valid medical scan."
                ),
            },
        )

    # 3. Run inference with selected model
    try:
        result = predict(str(saved_path), model_id=active_model["id"])
    except FileNotFoundError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Inference failed: {exc}")

    # 4. Generate Grad-CAM heatmap for selected model
    try:
        heatmap_path = generate_heatmap(str(saved_path), model_id=active_model["id"])
        heatmap_relative = str(Path(heatmap_path).relative_to(REPORTS_DIR.parent))
    except Exception as exc:
        print(f"[WARNING] Grad-CAM generation failed: {exc}")
        heatmap_path = None
        heatmap_relative = None

    # 5. Generate LLM clinical report (Grok)
    try:
        report_text = generate_report(
            predicted_class=result["predicted_class"],
            confidence=result["confidence"],
            model_id=active_model["id"],
        )
    except Exception as exc:
        print(f"[WARNING] Report generation failed: {exc}")
        report_text = None

    # 6. Persist to database
    db_prediction = Prediction(
        image_filename=file.filename or saved_filename,
        predicted_class=result["predicted_class"],
        confidence=result["confidence"],
        probabilities=json.dumps(result.get("probabilities")),
        model_id=active_model["id"],
        report_text=report_text,
        heatmap_path=heatmap_relative,
    )
    db.add(db_prediction)
    db.commit()
    db.refresh(db_prediction)

    # Construct response manually to avoid Pydantic failing on JSON string
    probs_dict = json.loads(db_prediction.probabilities) if db_prediction.probabilities else None
    return PredictionResponse(
        id=db_prediction.id,
        image_filename=db_prediction.image_filename,
        predicted_class=db_prediction.predicted_class,
        confidence=db_prediction.confidence,
        probabilities=probs_dict,
        report_text=db_prediction.report_text,
        heatmap_path=db_prediction.heatmap_path,
        warning=db_prediction.warning,
        model_id=db_prediction.model_id,
        created_at=db_prediction.created_at,
    )


# ---------------------------------------------------------------------------
# History Endpoints
# ---------------------------------------------------------------------------

@app.get(
    "/history",
    response_model=List[PredictionHistoryItem],
    tags=["History"],
    summary="List all past predictions",
    description="Returns all prediction records sorted by most recent first.",
)
def list_predictions(db: Session = Depends(get_db)):
    predictions = (
        db.query(Prediction)
        .order_by(Prediction.created_at.desc())
        .all()
    )
    return [PredictionHistoryItem.model_validate(p) for p in predictions]


@app.get(
    "/history/{prediction_id}",
    response_model=PredictionDetail,
    tags=["History"],
    summary="Get full prediction details",
    description=(
        "Returns complete details for a single prediction including "
        "the full probability distribution, Grad-CAM heatmap path, and clinical report."
    ),
)
def get_prediction(prediction_id: int, db: Session = Depends(get_db)):
    """Return full details for one prediction record by ID.

    Raises 404 if the prediction does not exist.
    """
    prediction = db.query(Prediction).filter(Prediction.id == prediction_id).first()
    if prediction is None:
        raise HTTPException(status_code=404, detail="Prediction not found")

    probs_dict = json.loads(prediction.probabilities) if prediction.probabilities else None
    return PredictionDetail(
        id=prediction.id,
        image_filename=prediction.image_filename,
        predicted_class=prediction.predicted_class,
        confidence=prediction.confidence,
        probabilities=probs_dict,
        report_text=prediction.report_text,
        heatmap_path=prediction.heatmap_path,
        warning=prediction.warning,
        model_id=prediction.model_id,
        created_at=prediction.created_at,
    )


# ---------------------------------------------------------------------------
# Frontend Serving (Hugging Face Spaces / Single Container)
# ---------------------------------------------------------------------------

FRONTEND_DIST = Path("/app/static")

if FRONTEND_DIST.exists():
    # Mount frontend assets
    assets_dir = FRONTEND_DIST / "assets"
    if assets_dir.exists():
        app.mount("/assets", StaticFiles(directory=str(assets_dir)), name="frontend_assets")

    # Catch-all route to serve static files or fallback to index.html for SPA routing
    @app.get("/{full_path:path}", include_in_schema=False)
    async def serve_spa(full_path: str):
        path = FRONTEND_DIST / full_path
        if path.is_file():
            return FileResponse(path)
        return FileResponse(FRONTEND_DIST / "index.html")
