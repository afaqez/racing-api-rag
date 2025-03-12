from pytz import timezone
from app.core.logging import logger
from app.services.ingestion import full_ingestion_job
from app.services.vectorization import vectorize_all
from apscheduler.schedulers.background import BackgroundScheduler

def ingestion_job():
    full_ingestion_job()

def start_scheduler():
    tz = timezone("Asia/Karachi")  
    scheduler = BackgroundScheduler(timezone=tz)
    
    # Schedule full ingestion job every hour from 9AM to 6PM
    scheduler.add_job(ingestion_job, 'cron', hour='9-18', minute='00')
    
    # Schedule vectorization job every hour at minute 05
    scheduler.add_job(vectorize_all, 'cron', minute='05')
    
    scheduler.start()
    logger.info("Scheduler started. Full ingestion job scheduled every hour from 9AM to 6PM, and vectorization job scheduled at minute 05 every hour (Asia/Karachi).")
