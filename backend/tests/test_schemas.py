import pytest
from pydantic import ValidationError
from app.schemas import VehicleCreate, RecognizeResponse, VehicleResponse

def test_vehicle_create_valid():
    v = VehicleCreate(
        plate_number="34ABC123",
        plate_display="34 ABC 123",
        fuel_type="dizel",
    )
    assert v.fuel_type == "dizel"

def test_vehicle_create_invalid_fuel_type():
    with pytest.raises(ValidationError):
        VehicleCreate(
            plate_number="34ABC123",
            plate_display="34 ABC 123",
            fuel_type="elektrik",
        )

def test_vehicle_create_optional_fields():
    v = VehicleCreate(
        plate_number="34ABC123",
        plate_display="34 ABC 123",
        fuel_type="benzin",
    )
    assert v.brand is None
    assert v.model is None
    assert v.color is None

def test_recognize_response_known_vehicle():
    r = RecognizeResponse(
        plate_text="34 ABC 123",
        is_known=True,
        vehicle=VehicleResponse(
            id=1,
            plate_number="34ABC123",
            plate_display="34 ABC 123",
            fuel_type="dizel",
            brand="Toyota",
            model="Corolla",
            color="Beyaz",
        ),
        log_id=42,
    )
    assert r.is_known is True
    assert r.vehicle.fuel_type == "dizel"

def test_recognize_response_unknown_vehicle():
    r = RecognizeResponse(
        plate_text="34 ABC 123",
        is_known=False,
        vehicle=None,
        log_id=43,
    )
    assert r.vehicle is None
