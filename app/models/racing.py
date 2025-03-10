# app/models/racing.py
from sqlalchemy import Column, Integer, String, DateTime, JSON, Boolean
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()

class RaceCard(Base):
    __tablename__ = "racecards"
    
    id = Column(Integer, primary_key=True, index=True)
    race_id = Column(String, unique=True, index=True)
    course = Column(String, index=True)
    course_id = Column(String, index=True)
    date = Column(DateTime, index=True)
    off_time = Column(String)
    off_dt = Column(String)
    race_name = Column(String)
    distance = Column(String)
    distance_f = Column(String)
    region = Column(String)
    pattern = Column(String)
    race_class = Column(String)
    race_type = Column(String)
    age_band = Column(String)
    rating_band = Column(String)
    prize = Column(String)
    field_size = Column(String)
    going = Column(String)
    going_detailed = Column(String)
    surface = Column(String)
    jumps = Column(String)
    big_race = Column(Boolean)
    is_abandoned = Column(Boolean)
    raw_data = Column(JSON)
    
    # Relationships are defined in the HorseResult and RaceResult models using backref

    @classmethod
    def upsert_from_api(cls, db, data: dict):
        """Parse API data and upsert racecards into the database."""
        for item in data.get("racecards", []):
            race_id = item.get("race_id")
            if not race_id:
                continue  # Skip if no race_id
                
            instance = db.query(cls).filter(cls.race_id == race_id).first()
            if not instance:
                instance = cls(race_id=race_id)
                
            # Update all fields
            instance.course = item.get("course")
            instance.course_id = item.get("course_id")
            
            # Convert date string to datetime (assuming ISO format)
            date_str = item.get("date")
            try:
                instance.date = datetime.fromisoformat(date_str)
            except Exception:
                instance.date = datetime.utcnow()  # Fallback if parsing fails
                
            instance.off_time = item.get("off_time")
            instance.off_dt = item.get("off_dt")
            instance.race_name = item.get("race_name")
            instance.distance = item.get("distance")
            instance.distance_f = item.get("distance_f")
            instance.region = item.get("region")
            instance.pattern = item.get("pattern")
            instance.race_class = item.get("race_class")
            instance.race_type = item.get("type")
            instance.age_band = item.get("age_band")
            instance.rating_band = item.get("rating_band")
            instance.prize = item.get("prize")
            instance.field_size = item.get("field_size")
            instance.going = item.get("going")
            instance.going_detailed = item.get("going_detailed")
            instance.surface = item.get("surface")
            instance.jumps = item.get("jumps")
            instance.big_race = item.get("big_race")
            instance.is_abandoned = item.get("is_abandoned")
            instance.raw_data = item
            
            db.merge(instance)
            
            # Store odds data for each runner
            for runner in item.get("runners", []):
                horse_id = runner.get("horse_id")
                if not horse_id:
                    continue
                    
                # Store odds data
                for odds_data in runner.get("odds", []):
                    odds = Odds(
                        race_id=race_id,
                        horse_id=horse_id,
                        bookmaker=odds_data.get("bookmaker"),
                        fraction=odds_data.get("fraction"),
                        decimal=odds_data.get("decimal"),
                        timestamp=odds_data.get("timestamp")
                    )
                    db.merge(odds)
                    
        db.commit()


class Odds(Base):
    """Stores odds information for horses in races"""
    __tablename__ = "odds"
    
    id = Column(Integer, primary_key=True, index=True)
    race_id = Column(String, index=True)
    horse_id = Column(String, index=True)
    bookmaker = Column(String)
    fraction = Column(String)
    decimal = Column(String)
    timestamp = Column(String)
