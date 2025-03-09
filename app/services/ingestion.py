from app.core.logging import logger
from app.models.racing import RaceCard
from app.models.course import Course
from app.models.horse import Horse
from app.models.jockey import Jockey
from app.models.trainer import Trainer
from app.models.owner import Owner
from app.core.database import SessionLocal
from app.services.racing_api_client import RacingAPIClient



horse_names = []


# One of the main data sources is the RaceCard API
# Fetches racecards for today and all future racecards
# Prize is in the RaceCard API Call
def ingest_racecards(db):
    client = RacingAPIClient()
    logger.info("Fetching racecards data...")
    data = client.racecards_standard({"day": "today"})
    for racecard in data.get("racecards", []):
        print(f"Found {len(racecard.get('runners'))} runners in race {racecard.get('race_id')}")
        horse_names.append(racecard.get("runners")[0].get("horse_name"))
    RaceCard.upsert_from_api(db, data)

# Course data is missing Name and Region Codes in the main table
# Name and Region Codes are in the raw_data
def ingest_courses(db):
    client = RacingAPIClient()
    logger.info("Fetching courses data...")
    data = client.list_courses()
    Course.upsert_from_api(db, data)

# Horse ingestion is done by searching for a horse by name
# Use case: User searches for a horse by name
# We can get specific horse data by searching for a horse by name
def ingest_horses(db):
    client = RacingAPIClient()
    logger.info("Fetching horses data...")
    horse_names = ["Constitution Hill", "Another Horse"]  # Example horse names
    for name in horse_names:
        data = client.search_horses(name)
        Horse.upsert_from_api(db, data)

# Jockey ingestion is done by searching for a jockey by name
# Use case: User searches for a jockey by name
def ingest_jockeys(db):
    client = RacingAPIClient()
    logger.info("Fetching jockeys data...")
    jockey_names = ["Jockey One", "Jockey Two"]  # Example jockey names
    for name in jockey_names:
        data = client.search_jockeys(name)
        Jockey.upsert_from_api(db, data)

# Trainer ingestion is done by searching for a trainer by name
# Use case: User searches for a trainer by name
def ingest_trainers(db):
    client = RacingAPIClient()
    logger.info("Fetching trainers data...")
    trainer_names = ["Trainer One", "Trainer Two"]  # Example trainer names
    for name in trainer_names:
        data = client.search_trainers(name)
        Trainer.upsert_from_api(db, data)

# Owner ingestion is done by searching for an owner by name
# Use case: User searches for an owner by name
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
        ingest_racecards(db)
        # ingest_courses(db)
        # ingest_horses(db)
        # ingest_jockeys(db)
        # ingest_trainers(db)
        # ingest_owners(db)
        logger.info("Full ingestion job completed successfully.")
    except Exception as e:
        logger.error("Error during full ingestion job: %s", e)
        db.rollback()
    finally:
        db.close()
