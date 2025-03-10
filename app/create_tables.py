from sqlalchemy import text
from app.core.database import engine
from app.core.logging import logger

def create_tables():
    """Create all tables in the correct order using raw SQL"""
    logger.info("Creating database tables...")
    
    with engine.connect() as connection:
        # Create pgvector extension
        logger.info("Creating pgvector extension...")
        connection.execute(text("CREATE EXTENSION IF NOT EXISTS vector;"))
        
        # Create tables in the correct order
        logger.info("Creating tables...")
        
        # 1. Create horses table
        connection.execute(text("""
            CREATE TABLE IF NOT EXISTS horses (
                id SERIAL PRIMARY KEY,
                horse_id VARCHAR UNIQUE,
                name VARCHAR,
                dob VARCHAR,
                age VARCHAR,
                sex VARCHAR,
                sex_code VARCHAR,
                colour VARCHAR,
                colour_code VARCHAR,
                region VARCHAR,
                sire VARCHAR,
                sire_id VARCHAR,
                sire_region VARCHAR,
                dam VARCHAR,
                dam_id VARCHAR,
                dam_region VARCHAR,
                damsire VARCHAR,
                damsire_id VARCHAR,
                damsire_region VARCHAR,
                breeder VARCHAR,
                trainer VARCHAR,
                trainer_id VARCHAR,
                owner VARCHAR,
                owner_id VARCHAR,
                last_run VARCHAR,
                form VARCHAR,
                raw_data JSONB
            );
            CREATE INDEX IF NOT EXISTS idx_horses_horse_id ON horses(horse_id);
            CREATE INDEX IF NOT EXISTS idx_horses_name ON horses(name);
            CREATE INDEX IF NOT EXISTS idx_horses_sire_id ON horses(sire_id);
            CREATE INDEX IF NOT EXISTS idx_horses_dam_id ON horses(dam_id);
            CREATE INDEX IF NOT EXISTS idx_horses_damsire_id ON horses(damsire_id);
            CREATE INDEX IF NOT EXISTS idx_horses_trainer_id ON horses(trainer_id);
            CREATE INDEX IF NOT EXISTS idx_horses_owner_id ON horses(owner_id);
        """))
        
        # 2. Create racecards table
        connection.execute(text("""
            CREATE TABLE IF NOT EXISTS racecards (
                id SERIAL PRIMARY KEY,
                race_id VARCHAR UNIQUE,
                course VARCHAR,
                course_id VARCHAR,
                date TIMESTAMP,
                off_time VARCHAR,
                off_dt VARCHAR,
                race_name VARCHAR,
                distance VARCHAR,
                distance_f VARCHAR,
                region VARCHAR,
                pattern VARCHAR,
                race_class VARCHAR,
                race_type VARCHAR,
                age_band VARCHAR,
                rating_band VARCHAR,
                prize VARCHAR,
                field_size VARCHAR,
                going VARCHAR,
                going_detailed VARCHAR,
                surface VARCHAR,
                jumps VARCHAR,
                big_race BOOLEAN,
                is_abandoned BOOLEAN,
                raw_data JSONB
            );
            CREATE INDEX IF NOT EXISTS idx_racecards_race_id ON racecards(race_id);
            CREATE INDEX IF NOT EXISTS idx_racecards_course ON racecards(course);
            CREATE INDEX IF NOT EXISTS idx_racecards_course_id ON racecards(course_id);
            CREATE INDEX IF NOT EXISTS idx_racecards_date ON racecards(date);
        """))
        
        # 3. Create horse_embeddings table
        connection.execute(text("""
            CREATE TABLE IF NOT EXISTS horse_embeddings (
                id SERIAL PRIMARY KEY,
                horse_id VARCHAR UNIQUE REFERENCES horses(horse_id),
                embedding vector(1536)
            );
            CREATE INDEX IF NOT EXISTS idx_horse_embeddings_horse_id ON horse_embeddings(horse_id);
        """))
        
        # 4. Create racecard_embeddings table
        connection.execute(text("""
            CREATE TABLE IF NOT EXISTS racecard_embeddings (
                id SERIAL PRIMARY KEY,
                race_id VARCHAR UNIQUE REFERENCES racecards(race_id),
                embedding vector(1536)
            );
            CREATE INDEX IF NOT EXISTS idx_racecard_embeddings_race_id ON racecard_embeddings(race_id);
        """))
        
        # 5. Create results table
        connection.execute(text("""
            CREATE TABLE IF NOT EXISTS results (
                id SERIAL PRIMARY KEY,
                race_id VARCHAR REFERENCES racecards(race_id),
                horse_id VARCHAR REFERENCES horses(horse_id),
                position VARCHAR,
                sp VARCHAR,
                sp_dec FLOAT,
                draw VARCHAR,
                btn VARCHAR,
                ovr_btn VARCHAR,
                weight VARCHAR,
                weight_lbs VARCHAR,
                headgear VARCHAR,
                time VARCHAR,
                or_rating VARCHAR,
                rpr VARCHAR,
                tsr VARCHAR,
                prize VARCHAR,
                jockey VARCHAR,
                jockey_id VARCHAR,
                jockey_claim_lbs VARCHAR,
                trainer VARCHAR,
                trainer_id VARCHAR,
                owner VARCHAR,
                owner_id VARCHAR,
                comment VARCHAR,
                raw_data JSONB
            );
            CREATE INDEX IF NOT EXISTS idx_results_race_id ON results(race_id);
            CREATE INDEX IF NOT EXISTS idx_results_horse_id ON results(horse_id);
            CREATE INDEX IF NOT EXISTS idx_results_jockey_id ON results(jockey_id);
            CREATE INDEX IF NOT EXISTS idx_results_trainer_id ON results(trainer_id);
            CREATE INDEX IF NOT EXISTS idx_results_owner_id ON results(owner_id);
        """))
        
        # 6. Create race_results table
        connection.execute(text("""
            CREATE TABLE IF NOT EXISTS race_results (
                id SERIAL PRIMARY KEY,
                race_id VARCHAR UNIQUE REFERENCES racecards(race_id),
                date VARCHAR,
                course VARCHAR,
                course_id VARCHAR,
                off_time VARCHAR,
                race_name VARCHAR,
                race_type VARCHAR,
                race_class VARCHAR,
                pattern VARCHAR,
                rating_band VARCHAR,
                age_band VARCHAR,
                distance VARCHAR,
                going VARCHAR,
                surface VARCHAR,
                winning_time VARCHAR,
                comments VARCHAR,
                raw_data JSONB
            );
            CREATE INDEX IF NOT EXISTS idx_race_results_race_id ON race_results(race_id);
        """))
        
        # 7. Create other tables
        # Courses
        connection.execute(text("""
            CREATE TABLE IF NOT EXISTS courses (
                id SERIAL PRIMARY KEY,
                course_id VARCHAR UNIQUE,
                name VARCHAR,
                country VARCHAR,
                region VARCHAR,
                type VARCHAR,
                raw_data JSONB
            );
            CREATE INDEX IF NOT EXISTS idx_courses_course_id ON courses(course_id);
        """))
        
        # Odds
        connection.execute(text("""
            CREATE TABLE IF NOT EXISTS odds (
                id SERIAL PRIMARY KEY,
                race_id VARCHAR,
                horse_id VARCHAR,
                bookmaker VARCHAR,
                fraction VARCHAR,
                decimal VARCHAR,
                timestamp VARCHAR
            );
            CREATE INDEX IF NOT EXISTS idx_odds_race_id ON odds(race_id);
            CREATE INDEX IF NOT EXISTS idx_odds_horse_id ON odds(horse_id);
        """))
        
        # Sessions
        connection.execute(text("""
            CREATE TABLE IF NOT EXISTS sessions (
                id SERIAL PRIMARY KEY,
                session_id VARCHAR UNIQUE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_active TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            CREATE INDEX IF NOT EXISTS idx_sessions_session_id ON sessions(session_id);
        """))
        
        # Chat history
        connection.execute(text("""
            CREATE TABLE IF NOT EXISTS chat_history (
                id SERIAL PRIMARY KEY,
                session_id VARCHAR REFERENCES sessions(session_id),
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                role VARCHAR,
                content TEXT
            );
            CREATE INDEX IF NOT EXISTS idx_chat_history_session_id ON chat_history(session_id);
        """))
        
        connection.commit()
    
    logger.info("All tables created successfully")

if __name__ == "__main__":
    create_tables()