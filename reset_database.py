from sqlalchemy import text
from app.core.database import engine
from app.core.logging import logger

def reset_database():
    """Drop and recreate all tables using raw SQL."""
    try:
        logger.info("Dropping all tables...")
        
        with engine.connect() as connection:
            # Disable foreign key checks temporarily
            connection.execute(text("SET session_replication_role = 'replica';"))
            
            # Drop all tables in one go
            connection.execute(text("""
                DROP TABLE IF EXISTS 
                    results, 
                    race_results, 
                    odds, 
                    racecard_embeddings, 
                    racecards, 
                    horses, 
                    jockeys, 
                    trainers, 
                    owners, 
                    courses, 
                    chat_sessions 
                CASCADE;
            """))
            
            logger.info("All tables dropped successfully.")
            
            # Create tables using raw SQL in the correct order
            logger.info("Recreating tables...")
            
            # Create courses table
            connection.execute(text("""
                CREATE TABLE courses (
                    id SERIAL PRIMARY KEY,
                    course_id TEXT UNIQUE,
                    name TEXT,
                    region_codes JSONB,
                    raw_data JSONB
                );
                CREATE INDEX ix_courses_course_id ON courses (course_id);
            """))
            
            # Create horses table
            connection.execute(text("""
                CREATE TABLE horses (
                    id SERIAL PRIMARY KEY,
                    horse_id TEXT UNIQUE,
                    name TEXT,
                    dob TEXT,
                    age TEXT,
                    sex TEXT,
                    sex_code TEXT,
                    colour TEXT,
                    colour_code TEXT,
                    region TEXT,
                    sire TEXT,
                    sire_id TEXT,
                    sire_region TEXT,
                    dam TEXT,
                    dam_id TEXT,
                    dam_region TEXT,
                    damsire TEXT,
                    damsire_id TEXT,
                    damsire_region TEXT,
                    breeder TEXT,
                    trainer TEXT,
                    trainer_id TEXT,
                    owner TEXT,
                    owner_id TEXT,
                    last_run TEXT,
                    form TEXT,
                    raw_data JSONB
                );
                CREATE INDEX ix_horses_horse_id ON horses (horse_id);
                CREATE INDEX ix_horses_name ON horses (name);
                CREATE INDEX ix_horses_sire_id ON horses (sire_id);
                CREATE INDEX ix_horses_dam_id ON horses (dam_id);
                CREATE INDEX ix_horses_damsire_id ON horses (damsire_id);
                CREATE INDEX ix_horses_trainer_id ON horses (trainer_id);
                CREATE INDEX ix_horses_owner_id ON horses (owner_id);
            """))
            
            # Create jockeys table
            connection.execute(text("""
                CREATE TABLE jockeys (
                    id SERIAL PRIMARY KEY,
                    jockey_id TEXT UNIQUE,
                    name TEXT,
                    raw_data JSONB
                );
                CREATE INDEX ix_jockeys_jockey_id ON jockeys (jockey_id);
            """))
            
            # Create trainers table
            connection.execute(text("""
                CREATE TABLE trainers (
                    id SERIAL PRIMARY KEY,
                    trainer_id TEXT UNIQUE,
                    name TEXT,
                    raw_data JSONB
                );
                CREATE INDEX ix_trainers_trainer_id ON trainers (trainer_id);
            """))
            
            # Create owners table
            connection.execute(text("""
                CREATE TABLE owners (
                    id SERIAL PRIMARY KEY,
                    owner_id TEXT UNIQUE,
                    name TEXT,
                    raw_data JSONB
                );
                CREATE INDEX ix_owners_owner_id ON owners (owner_id);
            """))
            
            # Create chat_sessions table
            connection.execute(text("""
                CREATE TABLE chat_sessions (
                    id SERIAL PRIMARY KEY,
                    session_id TEXT UNIQUE,
                    user_id TEXT,
                    chat_history TEXT,
                    last_updated TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP
                );
                CREATE INDEX ix_chat_sessions_session_id ON chat_sessions (session_id);
                CREATE INDEX ix_chat_sessions_user_id ON chat_sessions (user_id);
            """))
            
            # Create racecard_embeddings table
            connection.execute(text("""
                CREATE TABLE racecard_embeddings (
                    id SERIAL PRIMARY KEY,
                    race_id TEXT UNIQUE,
                    embedding vector(1536),
                    created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP
                );
                CREATE INDEX ix_racecard_embeddings_race_id ON racecard_embeddings (race_id);
            """))
            
            # Create racecards table
            connection.execute(text("""
                CREATE TABLE racecards (
                    id SERIAL PRIMARY KEY,
                    race_id TEXT UNIQUE,
                    course TEXT,
                    course_id TEXT,
                    date TIMESTAMP WITHOUT TIME ZONE,
                    off_time TEXT,
                    off_dt TEXT,
                    race_name TEXT,
                    distance TEXT,
                    distance_f TEXT,
                    region TEXT,
                    pattern TEXT,
                    race_class TEXT,
                    race_type TEXT,
                    age_band TEXT,
                    rating_band TEXT,
                    prize TEXT,
                    field_size TEXT,
                    going TEXT,
                    going_detailed TEXT,
                    surface TEXT,
                    jumps TEXT,
                    big_race BOOLEAN,
                    is_abandoned BOOLEAN,
                    raw_data JSONB
                );
                CREATE INDEX ix_racecards_race_id ON racecards (race_id);
                CREATE INDEX ix_racecards_course ON racecards (course);
                CREATE INDEX ix_racecards_course_id ON racecards (course_id);
                CREATE INDEX ix_racecards_date ON racecards (date);
            """))
            
            # Create odds table
            connection.execute(text("""
                CREATE TABLE odds (
                    id SERIAL PRIMARY KEY,
                    race_id TEXT,
                    horse_id TEXT,
                    bookmaker TEXT,
                    fraction TEXT,
                    decimal TEXT,
                    timestamp TEXT
                );
                CREATE INDEX ix_odds_race_id ON odds (race_id);
                CREATE INDEX ix_odds_horse_id ON odds (horse_id);
            """))
            
            # Create results table
            connection.execute(text("""
                CREATE TABLE results (
                    id SERIAL PRIMARY KEY,
                    race_id TEXT REFERENCES racecards(race_id),
                    horse_id TEXT REFERENCES horses(horse_id),
                    position TEXT,
                    sp TEXT,
                    sp_dec FLOAT,
                    draw TEXT,
                    btn TEXT,
                    ovr_btn TEXT,
                    weight TEXT,
                    weight_lbs TEXT,
                    headgear TEXT,
                    time TEXT,
                    or_rating TEXT,
                    rpr TEXT,
                    tsr TEXT,
                    prize TEXT,
                    jockey TEXT,
                    jockey_id TEXT,
                    jockey_claim_lbs TEXT,
                    trainer TEXT,
                    trainer_id TEXT,
                    owner TEXT,
                    owner_id TEXT,
                    comment TEXT,
                    raw_data JSONB
                );
                CREATE INDEX ix_results_race_id ON results (race_id);
                CREATE INDEX ix_results_horse_id ON results (horse_id);
                CREATE INDEX ix_results_jockey_id ON results (jockey_id);
                CREATE INDEX ix_results_trainer_id ON results (trainer_id);
                CREATE INDEX ix_results_owner_id ON results (owner_id);
            """))
            
            # Create race_results table
            connection.execute(text("""
                CREATE TABLE race_results (
                    id SERIAL PRIMARY KEY,
                    race_id TEXT REFERENCES racecards(race_id) UNIQUE,
                    date TEXT,
                    course TEXT,
                    course_id TEXT,
                    off_time TEXT,
                    race_name TEXT,
                    race_type TEXT,
                    race_class TEXT,
                    pattern TEXT,
                    rating_band TEXT,
                    age_band TEXT,
                    distance TEXT,
                    going TEXT,
                    surface TEXT,
                    winning_time TEXT,
                    comments TEXT,
                    raw_data JSONB
                );
                CREATE INDEX ix_race_results_race_id ON race_results (race_id);
            """))
            
            # Re-enable foreign key checks
            connection.execute(text("SET session_replication_role = 'origin';"))
            
            # Commit the transaction
            connection.commit()
            logger.info("All tables recreated successfully.")
            
    except Exception as e:
        logger.error(f"Error during database reset: {e}")
        raise

if __name__ == "__main__":
    reset_database()
    print("Database has been reset successfully.")