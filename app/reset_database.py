from sqlalchemy import text
from app.core.database import engine
from app.core.logging import logger

def reset_database():
    """Drop and recreate all tables in the database"""
    logger.info("Resetting database...")
    
    with engine.connect() as connection:
        # Disable foreign key checks temporarily
        connection.execute(text("SET session_replication_role = 'replica';"))
        
        # Drop all tables with CASCADE to handle dependencies
        logger.info("Dropping all tables...")
        connection.execute(text("""
            DROP TABLE IF EXISTS 
                horse_embeddings, 
                racecard_embeddings, 
                results, 
                race_results, 
                odds, 
                racecards, 
                horses, 
                courses, 
                jockeys, 
                trainers, 
                owners, 
                sessions,
                chat_history
            CASCADE;
        """))
        
        # Re-enable foreign key checks
        connection.execute(text("SET session_replication_role = 'origin';"))
        
        # Create pgvector extension
        logger.info("Creating pgvector extension...")
        connection.execute(text("CREATE EXTENSION IF NOT EXISTS vector;"))
        
        connection.commit()
    
    logger.info("All tables dropped successfully")
    
    # Import and create tables in the correct order
    from app.models import (
        course as course_models,
        horse as horse_models,
        jockey as jockey_models,
        trainer as trainer_models,
        owner as owner_models,
        session as session_models,
        racing as racing_models,
        embedding as embedding_models,
        result as result_models,
    )
    
    # Create tables in the correct order
    logger.info("Creating tables...")
    
    # First create tables without foreign key dependencies
    course_models.Base.metadata.create_all(bind=engine)
    horse_models.Base.metadata.create_all(bind=engine)
    jockey_models.Base.metadata.create_all(bind=engine)
    trainer_models.Base.metadata.create_all(bind=engine)
    owner_models.Base.metadata.create_all(bind=engine)
    session_models.Base.metadata.create_all(bind=engine)
    racing_models.Base.metadata.create_all(bind=engine)
    
    # Now create tables with foreign key dependencies
    embedding_models.Base.metadata.create_all(bind=engine)
    result_models.Base.metadata.create_all(bind=engine)
    
    logger.info("Database reset completed successfully")

if __name__ == "__main__":
    reset_database() 