from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from sqlalchemy import func

from app.config import settings
from app.database import get_db
from app.models import Vehicle
from app.schemas import VehicleCreate, VehicleUpdate, VehicleResponse, PaginatedVehicles

router = APIRouter()


@router.post("/api/vehicles", status_code=201, response_model=VehicleResponse)
def create_vehicle(vehicle: VehicleCreate, db: Session = Depends(get_db)):
    db_vehicle = Vehicle(**vehicle.model_dump())
    try:
        db.add(db_vehicle)
        db.commit()
        db.refresh(db_vehicle)
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="Vehicle with this plate already exists")
    return db_vehicle


@router.put("/api/vehicles/{vehicle_id}", response_model=VehicleResponse)
def update_vehicle(vehicle_id: int, updates: VehicleUpdate, db: Session = Depends(get_db)):
    vehicle = db.query(Vehicle).filter(Vehicle.id == vehicle_id).first()
    if not vehicle:
        raise HTTPException(status_code=404, detail="Vehicle not found")
    update_data = updates.model_dump(exclude_none=True)
    for key, value in update_data.items():
        setattr(vehicle, key, value)
    db.commit()
    db.refresh(vehicle)
    return vehicle


@router.get("/api/vehicles", response_model=PaginatedVehicles)
def list_vehicles(
    skip: int = Query(0, ge=0),
    limit: int = Query(settings.default_page_size, ge=1, le=settings.max_page_size),
    db: Session = Depends(get_db),
):
    total = db.query(func.count(Vehicle.id)).scalar()
    items = (
        db.query(Vehicle)
        .order_by(Vehicle.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )
    return PaginatedVehicles(
        items=[VehicleResponse.model_validate(v) for v in items],
        total=total,
        skip=skip,
        limit=limit,
    )
