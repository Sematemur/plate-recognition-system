from sqlalchemy import (
    Column, Integer, String, Float, Boolean, ForeignKey, DateTime,
    CheckConstraint, Index, func,
)
from app.database import Base


class Vehicle(Base):
    __tablename__ = "vehicles"

    id = Column(Integer, primary_key=True, index=True)
    plate_number = Column(String(15), unique=True, nullable=False, index=True)
    plate_display = Column(String(20), nullable=False)
    fuel_type = Column(String(10), nullable=False)
    brand = Column(String(50), nullable=True)
    model = Column(String(50), nullable=True)
    color = Column(String(30), nullable=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    __table_args__ = (
        CheckConstraint(
            "fuel_type IN ('benzin', 'dizel', 'lpg')",
            name="valid_fuel_type",
        ),
    )


class RecognitionLog(Base):
    __tablename__ = "recognition_logs"

    id = Column(Integer, primary_key=True, index=True)
    image_path = Column(String(255), nullable=True)
    plate_detected = Column(String(20), nullable=True)
    plate_confirmed = Column(String(20), nullable=True)
    vehicle_id = Column(Integer, ForeignKey("vehicles.id"), nullable=True, index=True)
    is_known = Column(Boolean, nullable=True)
    confidence = Column(Float, nullable=True)
    det_confidence = Column(Float, nullable=True)
    created_at = Column(DateTime, server_default=func.now())

    __table_args__ = (
        CheckConstraint(
            "confidence IS NULL OR (confidence >= 0 AND confidence <= 1)",
            name="valid_confidence",
        ),
        CheckConstraint(
            "det_confidence IS NULL OR (det_confidence >= 0 AND det_confidence <= 1)",
            name="valid_det_confidence",
        ),
        Index("ix_recognition_logs_created_at", "created_at"),
    )
