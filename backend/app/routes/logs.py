from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.config import settings
from app.database import get_db
from app.models import RecognitionLog
from app.schemas import LogConfirmRequest, LogResponse, PaginatedLogs

router = APIRouter()


@router.get("/api/logs", response_model=PaginatedLogs)
def list_logs(
    skip: int = Query(0, ge=0),
    limit: int = Query(settings.default_page_size, ge=1, le=settings.max_page_size),
    db: Session = Depends(get_db),
):
    total = db.query(func.count(RecognitionLog.id)).scalar()
    items = (
        db.query(RecognitionLog)
        .order_by(RecognitionLog.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )
    return PaginatedLogs(
        items=[LogResponse.model_validate(log) for log in items],
        total=total,
        skip=skip,
        limit=limit,
    )


@router.patch("/api/logs/{log_id}/confirm")
def confirm_log(log_id: int, request: LogConfirmRequest, db: Session = Depends(get_db)):
    log = db.query(RecognitionLog).filter(RecognitionLog.id == log_id).first()
    if not log:
        raise HTTPException(status_code=404, detail="Log not found")
    log.plate_confirmed = request.plate_confirmed
    db.commit()
    return {"success": True}
