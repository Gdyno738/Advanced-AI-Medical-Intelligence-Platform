"""
SQLAlchemy ORM model for the Prediction table.

Stores the results of each chest X-ray analysis including the predicted
class, confidence score, generated report, and path to the Grad-CAM heatmap.
"""

from datetime import datetime, timezone

from sqlalchemy import Column, Integer, String, Float, Text, DateTime
from sqlalchemy.orm import declarative_base

Base = declarative_base()


class Prediction(Base):
    """Represents a single chest X-ray prediction record.

    Attributes:
        id: Auto-incremented primary key.
        image_filename: Original filename of the uploaded X-ray image.
        predicted_class: Model prediction (e.g. "NORMAL" or "PNEUMONIA").
        confidence: Model confidence score between 0 and 1.
        report_text: LLM-generated medical analysis report.
        heatmap_path: File path to the saved Grad-CAM overlay image.
        created_at: Timestamp when the prediction was created (UTC).
    """

    __tablename__ = "predictions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    image_filename = Column(String(255), nullable=False)
    predicted_class = Column(String(50), nullable=False)
    confidence = Column(Float, nullable=False)
    probabilities = Column(Text, nullable=True)   # JSON: {"NORMAL": 0.03, "PNEUMONIA": 0.97}
    model_id = Column(String(100), nullable=True)  # registry key, e.g. "chest_xray_pneumonia"
    report_text = Column(Text, nullable=True)
    heatmap_path = Column(String(500), nullable=True)
    warning = Column(Text, nullable=True)
    created_at = Column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    def __repr__(self) -> str:
        return (
            f"<Prediction(id={self.id}, class='{self.predicted_class}', "
            f"confidence={self.confidence:.2f})>"
        )
