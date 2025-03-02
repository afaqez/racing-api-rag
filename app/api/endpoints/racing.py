# app/api/endpoints/racing.py
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.racing import RaceCard
from fastapi import APIRouter, Depends, HTTPException
from app.core.logging import logger

router = APIRouter()


@router.get("/racecards", summary="Get list of racecards from database")
def get_racecards(db: Session = Depends(get_db)):
    logger.info("Getting racecards from database")
    racecards = db.query(RaceCard).all()
    logger.info(f"Found {len(racecards)} racecards")
    return racecards[:10]


@router.get("/racecards/{race_id}", summary="Get racecard details by race_id")
def get_racecard(race_id: str, db: Session = Depends(get_db)):
    racecard = db.query(RaceCard).filter(RaceCard.race_id == race_id).first()
    if not racecard:
        raise HTTPException(status_code=404, detail="Racecard not found")
    return racecard
