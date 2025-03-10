from app.core.logging import logger
from app.models.racing import RaceCard, Odds
from app.models.course import Course
from app.models.horse import Horse
from app.models.jockey import Jockey
from app.models.trainer import Trainer
from app.models.owner import Owner
from app.models.result import HorseResult, RaceResult
from app.core.database import SessionLocal
from app.services.racing_api_client import RacingAPIClient
from datetime import datetime, timedelta

# One of the main data sources is the RaceCard API
# Fetches racecards for today and all future racecards
def ingest_racecards(db):
    client = RacingAPIClient()
    logger.info("Fetching racecards data...")
    data = client.racecards_standard({"day": "today"})
    
    # Log the number of racecards and runners
    racecards = data.get("racecards", [])
    logger.info(f"Found {len(racecards)} racecards")
    
    total_runners = 0
    race_ids = []
    horse_ids = []  # Track horse IDs to avoid duplicates
    
    for racecard in racecards:
        runners = racecard.get("runners", [])
        race_id = racecard.get("race_id")
        if race_id:
            race_ids.append(race_id)
        
        # Process all runners to extract horse data
        for runner in runners:
            horse_id = runner.get("horse_id")
            if horse_id and horse_id not in horse_ids:
                horse_ids.append(horse_id)
                # Store horse data directly from runner
                Horse.upsert_from_api(db, runner)
        
        total_runners += len(runners)
        logger.info(f"Race {race_id}: {len(runners)} runners")
    
    logger.info(f"Total runners across all races: {total_runners}")
    logger.info(f"Extracted data for {len(horse_ids)} unique horses")
    
    # Upsert the racecard data
    RaceCard.upsert_from_api(db, data)
    
    return race_ids

# Ingest race results using race_ids from racecards
def ingest_results(db, race_ids=None):
    client = RacingAPIClient()
    logger.info("Fetching race results...")
    
    # If no race_ids provided, get recent results
    if not race_ids:
        # Get results from the last 7 days
        results_data = client.list_results({"limit": 100})
        if "results" in results_data:
            for result_summary in results_data.get("results", []):
                race_id = result_summary.get("race_id")
                if race_id:
                    try:
                        detailed_result = client.result(race_id)
                        HorseResult.upsert_from_api(db, detailed_result)
                        logger.info(f"Ingested results for race {race_id}")
                    except Exception as e:
                        logger.error(f"Error fetching results for race {race_id}: {e}")
    else:
        # Try to get results for specific race_ids
        for race_id in race_ids:
            try:
                detailed_result = client.result(race_id)
                if detailed_result:
                    HorseResult.upsert_from_api(db, detailed_result)
                    logger.info(f"Ingested results for race {race_id}")
            except Exception as e:
                logger.error(f"Error fetching results for race {race_id}: {e}")

# Course data is missing Name and Region Codes in the main table
# Name and Region Codes are in the raw_data
def ingest_courses(db):
    client = RacingAPIClient()
    logger.info("Fetching courses data...")
    data = client.list_courses()
    Course.upsert_from_api(db, data)

# Horse ingestion is done by searching for a horse by name
# Use case: Get detailed data for all horses racing today
def ingest_horses(db, horse_ids=None):
    client = RacingAPIClient()
    logger.info("Fetching detailed horse data...")
    
    if not horse_ids:
        # Get all horses from today's racecards if no specific IDs provided
        try:
            # Query all horses that were added from today's racecards
            today = datetime.now().date()
            racecards = db.query(RaceCard).filter(
                RaceCard.date >= today,
                RaceCard.date < today + timedelta(days=1)
            ).all()
            
            horse_ids = []
            for racecard in racecards:
                # Extract horse IDs from raw_data to get all runners
                if racecard.raw_data and "runners" in racecard.raw_data:
                    for runner in racecard.raw_data["runners"]:
                        horse_id = runner.get("horse_id")
                        if horse_id and horse_id not in horse_ids:
                            horse_ids.append(horse_id)
            
            logger.info(f"Found {len(horse_ids)} unique horses in today's races")
            
            if not horse_ids:
                # If no horses found in racecards, try to get some from the database
                horses = db.query(Horse).limit(20).all()
                horse_ids = [horse.horse_id for horse in horses if horse.horse_id]
                logger.info(f"No horses in today's races, using {len(horse_ids)} from database")
                
        except Exception as e:
            logger.error(f"Error getting horses from today's racecards: {e}")
            return
    
    # Process all horse IDs (limit to 100 to avoid excessive API calls if needed)
    processed_count = 0
    for horse_id in horse_ids:
        try:
            # Get detailed horse data directly using the ID
            detailed_data = client.horse_pro(horse_id)
            Horse.upsert_from_api(db, detailed_data)
            processed_count += 1
            
            # Log progress every 10 horses
            if processed_count % 10 == 0:
                logger.info(f"Processed {processed_count}/{len(horse_ids[:100])} horses")
                
        except Exception as e:
            logger.error(f"Error fetching detailed data for horse ID {horse_id}: {e}")
    
    logger.info(f"Completed detailed data ingestion for {processed_count} horses")

# Jockey ingestion is done by searching for a jockey by name
def ingest_jockeys(db):
    client = RacingAPIClient()
    logger.info("Fetching jockeys data...")
    jockey_names = ["Jockey One", "Jockey Two"]  # Example jockey names
    for name in jockey_names:
        data = client.search_jockeys(name)
        Jockey.upsert_from_api(db, data)

# Trainer ingestion is done by searching for a trainer by name
def ingest_trainers(db):
    client = RacingAPIClient()
    logger.info("Fetching trainers data...")
    trainer_names = ["Trainer One", "Trainer Two"]  # Example trainer names
    for name in trainer_names:
        data = client.search_trainers(name)
        Trainer.upsert_from_api(db, data)

# Owner ingestion is done by searching for an owner by name
def ingest_owners(db):
    client = RacingAPIClient()
    logger.info("Fetching owners data...")
    owner_names = ["Owner One", "Owner Two"]  # Example owner names
    for name in owner_names:
        data = client.search_owners(name)
        Owner.upsert_from_api(db, data)

def full_ingestion_job():
    logger.info("Starting full ingestion job...")
    db = SessionLocal()
    try:
        # First ingest racecards to get race_ids and basic horse data
        race_ids = ingest_racecards(db)
        
        # Then try to get results for those races
        # ingest_results(db, race_ids)
        
        # # Also get some historical results
        # ingest_results(db)
        
        # Ingest courses for reference data
        ingest_courses(db)
        
        # Get detailed horse data for all horses in today's races
        # No need to pass horse_ids as the function will get them from today's racecards
        ingest_horses(db)
        
        # Optionally ingest other entities
        # ingest_jockeys(db)
        # ingest_trainers(db)
        # ingest_owners(db)
        
        logger.info("Full ingestion job completed successfully.")
    except Exception as e:
        logger.error(f"Error during full ingestion job: {e}")
        db.rollback()
    finally:
        db.close()
