# heartguard-backend/vitals_service/main.py
from fastapi import FastAPI, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from .database import get_db
from . import models, schemas
from .deps import current_user

app = FastAPI(title="HeartGuard Vitals Service")

@app.get("/api/vitals/latest", response_model=schemas.VitalOut)
def latest_vital(db: Session = Depends(get_db), user_id: int = Depends(current_user)):
    row = db.query(models.Vital).filter(models.Vital.user_id == user_id).order_by(models.Vital.measured_at.desc()).first()
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No vitals")
    return row

@app.get("/api/vitals", response_model=List[schemas.VitalOut])
def list_vitals(limit: int = 50, db: Session = Depends(get_db), user_id: int = Depends(current_user)):
    rows = (
        db.query(models.Vital)
        .filter(models.Vital.user_id == user_id)
        .order_by(models.Vital.measured_at.desc())
        .limit(limit)
        .all()
    )
    return rows

@app.post("/api/vitals", response_model=schemas.VitalOut)
def create_vital(body: schemas.VitalIn, db: Session = Depends(get_db), user_id: int = Depends(current_user)):
    row = models.Vital(user_id=user_id, **body.model_dump())
    db.add(row)
    db.commit()
    db.refresh(row)
    return row

@app.get("/api/vitals/health")
def health():
    return {"ok": True, "service": "vitals"}
