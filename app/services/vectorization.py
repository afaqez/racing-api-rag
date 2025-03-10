from app.core.database import SessionLocal
from app.models.racing import RaceCard
from app.models.horse import Horse
from app.models.embedding import RaceCardEmbedding, HorseEmbedding
from app.utils.embedding import generate_embedding
from app.core.logging import logger
from sqlalchemy import text


def vectorize_new_racecards():
    """
    Create rich embeddings incorporating all relevant race information
    """
    logger.info(f"Starting racecard vectorization job...")
    db = SessionLocal()
    try:
        # First check if the table exists
        table_exists = db.execute(text(
            "SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'racecard_embeddings')"
        )).scalar()
        
        if not table_exists:
            logger.warning("racecard_embeddings table does not exist. Skipping vectorization.")
            return
            
        racecards = db.query(RaceCard).all()
        count = 0
        total_processed = 0
        for rc in racecards:
            total_processed += 1
            
            # Check if embedding already exists
            existing = db.execute(
                text("SELECT 1 FROM racecard_embeddings WHERE race_id = :race_id"),
                {"race_id": rc.race_id}
            ).fetchone()
            
            if existing:
                continue

            # Create a comprehensive text representation
            text_components = [
                f"Race: {rc.race_name} at {rc.course}",
                f"Date: {rc.date}",
                f"Distance: {rc.distance}",
                f"Going: {rc.going}",
                f"Surface: {rc.surface}",
                f"Race Class: {rc.race_class}",
                f"Race Type: {rc.race_type}",
                f"Prize: {rc.prize}",
                "Runners:",
            ]

            # Add runner information from the raw_data
            runners = rc.raw_data.get("runners", []) if rc.raw_data else []
            for runner in runners:
                runner_info = [
                    f"  - Horse: {runner.get('horse', 'N/A')}",
                    f"    Jockey: {runner.get('jockey', 'N/A')}",
                    f"    Trainer: {runner.get('trainer', 'N/A')}",
                    f"    Weight: {runner.get('weight', 'N/A')}",
                    f"    Draw: {runner.get('draw', 'N/A')}",
                ]
                if runner.get("odds"):
                    odds_info = runner.get("odds", [])
                    if isinstance(odds_info, list) and len(odds_info) > 0:
                        runner_info.append(f"    Odds: {odds_info[0].get('fraction', 'N/A')}")
                text_components.extend(runner_info)

            # Join all components with proper spacing
            comprehensive_text = "\n".join(text_components)

            logger.info(f"Creating embedding for race: {rc.race_name}")
            embedding = generate_embedding(comprehensive_text)
            if embedding:
                # Insert using raw SQL
                db.execute(
                    text("""
                        INSERT INTO racecard_embeddings (race_id, embedding)
                        VALUES (:race_id, :embedding)
                        ON CONFLICT (race_id) DO UPDATE SET embedding = :embedding
                    """),
                    {"race_id": rc.race_id, "embedding": embedding}
                )
                count += 1

        db.commit()
        logger.info(
            f"Racecard vectorization complete. Added {count} new embeddings (processed {total_processed} records)"
        )
    except Exception as e:
        logger.error("Error during racecard vectorization job: %s", str(e))
        db.rollback()
    finally:
        db.close()


def vectorize_horses():
    """
    Create embeddings for horse information to enable horse-specific queries
    """
    logger.info(f"Starting horse vectorization job...")
    db = SessionLocal()
    try:
        # First check if the table exists
        table_exists = db.execute(text(
            "SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'horse_embeddings')"
        )).scalar()
        
        if not table_exists:
            logger.warning("horse_embeddings table does not exist. Skipping vectorization.")
            return
            
        horses = db.query(Horse).all()
        count = 0
        total_processed = 0
        
        for horse in horses:
            total_processed += 1
            
            # Check if embedding already exists
            existing = db.execute(
                text("SELECT 1 FROM horse_embeddings WHERE horse_id = :horse_id"),
                {"horse_id": horse.horse_id}
            ).fetchone()
            
            if existing:
                continue
                
            # Create comprehensive text representation of the horse
            text_components = [
                f"Horse: {horse.name}",
                f"ID: {horse.horse_id}",
            ]
            
            # Add basic information
            if horse.dob:
                text_components.append(f"Date of Birth: {horse.dob}")
            if horse.age:
                text_components.append(f"Age: {horse.age}")
            if horse.sex:
                text_components.append(f"Sex: {horse.sex}")
            if horse.colour:
                text_components.append(f"Colour: {horse.colour}")
            if horse.region:
                text_components.append(f"Region: {horse.region}")
                
            # Add pedigree information
            pedigree_info = []
            if horse.sire:
                pedigree_info.append(f"Sire: {horse.sire}")
            if horse.dam:
                pedigree_info.append(f"Dam: {horse.dam}")
            if horse.damsire:
                pedigree_info.append(f"Damsire: {horse.damsire}")
            if pedigree_info:
                text_components.append("Pedigree:")
                text_components.extend([f"  - {info}" for info in pedigree_info])
                
            # Add connections
            connections = []
            if horse.trainer:
                connections.append(f"Trainer: {horse.trainer}")
            if horse.owner:
                connections.append(f"Owner: {horse.owner}")
            if connections:
                text_components.append("Connections:")
                text_components.extend([f"  - {info}" for info in connections])
                
            # Add form information
            if horse.form:
                text_components.append(f"Form: {horse.form}")
            if horse.last_run:
                text_components.append(f"Last Run: {horse.last_run}")
                
            # Join all components with proper spacing
            comprehensive_text = "\n".join(text_components)
            
            logger.info(f"Creating embedding for horse: {horse.name}")
            embedding = generate_embedding(comprehensive_text)
            if embedding:
                # Insert using raw SQL
                db.execute(
                    text("""
                        INSERT INTO horse_embeddings (horse_id, embedding)
                        VALUES (:horse_id, :embedding)
                        ON CONFLICT (horse_id) DO UPDATE SET embedding = :embedding
                    """),
                    {"horse_id": horse.horse_id, "embedding": embedding}
                )
                count += 1
                
        db.commit()
        logger.info(
            f"Horse vectorization complete. Added {count} new embeddings (processed {total_processed} records)"
        )
    except Exception as e:
        logger.error("Error during horse vectorization job: %s", str(e))
        db.rollback()
    finally:
        db.close()
