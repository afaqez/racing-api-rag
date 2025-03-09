from fastapi import APIRouter, HTTPException
from app.services.ingestion import full_ingestion_job
from app.services.vectorization import vectorize_new_racecards
from app.core.logging import logger

router = APIRouter()


@router.post("/ingest", summary="Trigger the full ingestion job")
def trigger_ingestion():
    try:
        logger.info("Manually triggering ingestion job...")
        full_ingestion_job()
        vectorize_new_racecards()
        return {"message": "Ingestion job triggered successfully."}
    except Exception as e:
        logger.error(f"Error during ingestion job: {e}")
        raise HTTPException(status_code=500, detail="Ingestion job failed.")
