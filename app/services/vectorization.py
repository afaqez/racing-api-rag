from app.core.database import SessionLocal
from app.models.racing import RaceCard
from app.models.embedding import RaceCardEmbedding
from app.utils.embedding import generate_embedding
from app.core.logging import logger


def vectorize_new_racecards(limit: int = 10):
    """
    Create rich embeddings incorporating all relevant race information
    """
    logger.info(f"Starting vectorization job (limit: {limit})...")
    db = SessionLocal()
    try:
        racecards = db.query(RaceCard).all()
        count = 0
        total_processed = 0
        for rc in racecards:
            if count >= limit:
                break

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
                "Horses:",
            ]

            # Add horse information
            for horse in rc.horses:
                horse_info = [
                    f"  - Name: {horse.name}",
                    f"    Age: {horse.age} {horse.sex}",
                    f"    Breeding: by {horse.sire} out of {horse.dam}",
                    f"    Trainer: {horse.trainer} ({horse.trainer_location})",
                    f"    Recent form: {horse.form}",
                ]
                if horse.trainer_rtf:
                    horse_info.append(f"    Trainer RTF: {horse.trainer_rtf}")
                if horse.odds:
                    horse_info.append(f"    Current odds: {horse.odds}")
                text_components.extend(horse_info)

            # Join all components with proper spacing
            comprehensive_text = "\n".join(text_components)

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
