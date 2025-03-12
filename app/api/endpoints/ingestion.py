from fastapi import APIRouter, HTTPException
from app.services.ingestion import full_ingestion_job
from app.services.vectorization import vectorize_new_racecards, vectorize_horses
from app.core.logging import logger

router = APIRouter()


@router.post("/ingest", summary="Trigger the full ingestion job")
def trigger_ingestion():
    try:
        logger.info("Manually triggering ingestion job...")
        # Run the full ingestion job to get all data
        full_ingestion_job()
        
        # Vectorize both racecards and horses
        # logger.info("Starting vectorization of racecards and horses...")
        # vectorize_new_racecards()
        # vectorize_horses()
        # logger.info("Vectorization completed successfully")
        
        return {"message": "Ingestion and vectorization jobs completed successfully."}
    except Exception as e:
        logger.error(f"Error during ingestion or vectorization job: {e}")
        raise HTTPException(status_code=500, detail=f"Job failed: {str(e)}")


@router.post("/vectorize", summary="Trigger vectorization of existing data")
def trigger_vectorization():
    try:
        logger.info("Manually triggering vectorization job...")
        # Vectorize both racecards and horses
        vectorize_new_racecards()
        vectorize_horses()
        return {"message": "Vectorization job completed successfully."}
    except Exception as e:
        logger.error(f"Error during vectorization job: {e}")
        raise HTTPException(status_code=500, detail=f"Vectorization failed: {str(e)}")
