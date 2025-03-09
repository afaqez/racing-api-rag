from app.core.database import SessionLocal
from app.models.racing import RaceCard
from app.models.embedding import RaceCardEmbedding
from app.utils.embedding import generate_embedding
from app.core.logging import logger


def vectorize_new_racecards():
    """
    Create rich embeddings incorporating all relevant race information
    """
    logger.info(f"Starting vectorization job...")
    db = SessionLocal()
    try:
        racecards = db.query(RaceCard).all()
        count = 0
        total_processed = 0
        for rc in racecards:

            total_processed += 1
            existing = (
                db.query(RaceCardEmbedding)
                .filter(RaceCardEmbedding.race_id == rc.race_id)
                .first()
            )
            if existing:
                continue

            # Create a comprehensive text representation
            text_components = [
                f"Race: {rc.race_name} at {rc.course}",
                f"Date: {rc.date}",
                f"Distance: {rc.distance}",
                f"Going: {rc.going}",
                "Runners:",
            ]

            # Add runner information from the raw_data
            runners = rc.raw_data.get("runners", []) if rc.raw_data else []
            for runner in runners:
                runner_info = [
                    f"  - Horse: {runner.get('horse_name', 'N/A')}",
                    f"    Jockey: {runner.get('jockey_name', 'N/A')}",
                    f"    Trainer: {runner.get('trainer_name', 'N/A')}",
                    f"    Weight: {runner.get('weight', 'N/A')}",
                    f"    Draw: {runner.get('draw', 'N/A')}",
                ]
                if runner.get("odds"):
                    runner_info.append(f"    Odds: {runner.get('odds')}")
                text_components.extend(runner_info)

            # Join all components with proper spacing
            comprehensive_text = "\n".join(text_components)

            logger.info(f"Creating embedding for race: {rc.race_name}")
            embedding = generate_embedding(comprehensive_text)
            if embedding:
                new_embedding = RaceCardEmbedding(
                    race_id=rc.race_id, embedding=embedding
                )
                db.add(new_embedding)
                count += 1

        db.commit()
        logger.info(
            f"Vectorization complete. Added {count} new embeddings (processed {total_processed} records)"
        )
    except Exception as e:
        logger.error("Error during vectorization job: %s", str(e))
        db.rollback()
    finally:
        db.close()
