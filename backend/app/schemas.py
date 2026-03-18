from datetime import datetime
from enum import Enum
from pydantic import BaseModel, field_validator


class FuelType(str, Enum):
    benzin = "benzin"
    dizel = "dizel"
    lpg = "lpg"


class VehicleCreate(BaseModel):
    plate_number: str
    plate_display: str
    fuel_type: FuelType
    brand: str | None = None
    model: str | None = None
    color: str | None = None

    @field_validator("plate_number")
    @classmethod
    def validate_plate_number(cls, v: str) -> str:
        cleaned = v.replace(" ", "").upper()
        if len(cleaned) < 6 or len(cleaned) > 12:
            raise ValueError("Plate number must be 6-12 characters")
        return cleaned

    @field_validator("plate_display")
    @classmethod
    def validate_plate_display(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("Plate display cannot be empty")
        return v.strip()


class VehicleResponse(BaseModel):
    id: int
    plate_number: str
    plate_display: str
    fuel_type: str
    brand: str | None = None
    model: str | None = None
    color: str | None = None
    created_at: datetime | None = None

    class Config:
        from_attributes = True


class VehicleUpdate(BaseModel):
    fuel_type: FuelType | None = None
    brand: str | None = None
    model: str | None = None
    color: str | None = None


class RecognizeResponse(BaseModel):
    plate_text: str
    is_known: bool
    vehicle: VehicleResponse | None = None
    log_id: int


class LogConfirmRequest(BaseModel):
    plate_confirmed: str

    @field_validator("plate_confirmed")
    @classmethod
    def validate_plate(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("Plate confirmed cannot be empty")
        return v.strip()


class LogResponse(BaseModel):
    id: int
    plate_detected: str | None
    plate_confirmed: str | None
    vehicle_id: int | None
    is_known: bool | None
    created_at: datetime | None

    class Config:
        from_attributes = True


class PaginatedLogs(BaseModel):
    items: list[LogResponse]
    total: int
    skip: int
    limit: int


class PaginatedVehicles(BaseModel):
    items: list[VehicleResponse]
    total: int
    skip: int
    limit: int


class ErrorResponse(BaseModel):
    success: bool = False
    error: str
    detail: str
