from sqlalchemy import text, create_engine
from sqlalchemy.orm import sessionmaker
from app.core.logging import logger
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Create a direct connection to the database using localhost
DB_USER = os.getenv("POSTGRES_USER", "postgres")
DB_PASSWORD = os.getenv("POSTGRES_PASSWORD", "postgres")
DB_NAME = os.getenv("POSTGRES_DB", "postgres")
DB_HOST = "localhost"  # Use localhost instead of container name
DB_PORT = "5436"  # Use the mapped port from docker-compose

DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

# Create engine and session
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def clear_all_tables():
    """Delete all data from all tables in the database using raw SQL."""
    db = SessionLocal()
    try:
        logger.info("Starting database cleanup...")
        logger.info(f"Connecting to database at: {DB_HOST}:{DB_PORT}")
        
        # List of tables in dependency order (child tables first)
        tables = [
            "racecard_embeddings",
            "racecards",
            "horses",
            "jockeys",
            "trainers",
            "owners",
            "courses",
            "chat_sessions"
        ]
        
        with engine.connect() as connection:
            # Disable foreign key checks temporarily
            connection.execute(text("SET session_replication_role = 'replica';"))
            
            # Truncate all tables
            for table in tables:
                connection.execute(text(f"TRUNCATE TABLE {table} CASCADE;"))
                logger.info(f"Truncated table: {table}")
            
            # Reset sequences
            for table in tables:
                try:
                    connection.execute(text(f"ALTER SEQUENCE {table}_id_seq RESTART WITH 1;"))
                    logger.info(f"Reset sequence for {table}")
                except Exception as e:
                    logger.warning(f"Could not reset sequence for {table}: {e}")
            
            # Re-enable foreign key checks
            connection.execute(text("SET session_replication_role = 'origin';"))
            
            # Commit the transaction
            connection.commit()
            logger.info("All tables have been cleared successfully.")
            
    except Exception as e:
        logger.error(f"Error during database cleanup: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    clear_all_tables()
    print("Database cleanup completed.")