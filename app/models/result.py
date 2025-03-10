from sqlalchemy import Column, Integer, String, DateTime, JSON, Float, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, backref
from datetime import datetime

Base = declarative_base()

class HorseResult(Base):
    __tablename__ = "results"
    
    id = Column(Integer, primary_key=True, index=True)
    race_id = Column(String, ForeignKey("racecards.race_id"), index=True)
    horse_id = Column(String, ForeignKey("horses.horse_id"), index=True)
    position = Column(String)
    sp = Column(String)  # Starting price
    sp_dec = Column(Float)  # Decimal odds
    draw = Column(String)
    btn = Column(String)  # Beaten by
    ovr_btn = Column(String)  # Overall beaten by
    weight = Column(String)
    weight_lbs = Column(String)
    headgear = Column(String)
    time = Column(String)
    or_rating = Column(String)  # Official rating
    rpr = Column(String)  # Racing Post Rating
    tsr = Column(String)  # Timeform Speed Rating
    prize = Column(String)
    jockey = Column(String)
    jockey_id = Column(String, index=True)
    jockey_claim_lbs = Column(String)
    trainer = Column(String)
    trainer_id = Column(String, index=True)
    owner = Column(String)
    owner_id = Column(String, index=True)
    comment = Column(String)
    raw_data = Column(JSON)  # Store the complete runner data
    
    # Use string references instead of direct class references
    # This avoids the circular dependency issue
    race = relationship("RaceCard", foreign_keys=[race_id], 
                        backref=backref("results", uselist=True))
    horse = relationship("Horse", foreign_keys=[horse_id], 
                         backref=backref("results", uselist=True))
    
    @classmethod
    def upsert_from_api(cls, db, race_data: dict):
        """Parse API result data and upsert results into the database."""
        race_id = race_data.get("race_id")
        if not race_id:
            return  # Skip if no race_id
            
        # First, delete any existing results for this race to avoid duplicates
        db.query(cls).filter(cls.race_id == race_id).delete()
        
        for runner in race_data.get("runners", []):
            horse_id = runner.get("horse_id")
            if not horse_id:
                continue  # Skip if no horse_id
                
            result = cls(
                race_id=race_id,
                horse_id=horse_id,
                position=runner.get("position"),
                sp=runner.get("sp"),
                sp_dec=float(runner.get("sp_dec", 0)) if runner.get("sp_dec") else None,
                draw=runner.get("draw"),
                btn=runner.get("btn"),
                ovr_btn=runner.get("ovr_btn"),
                weight=runner.get("weight"),
                weight_lbs=runner.get("weight_lbs"),
                headgear=runner.get("headgear"),
                time=runner.get("time"),
                or_rating=runner.get("or"),
                rpr=runner.get("rpr"),
                tsr=runner.get("tsr"),
                prize=runner.get("prize"),
                jockey=runner.get("jockey"),
                jockey_id=runner.get("jockey_id"),
                jockey_claim_lbs=runner.get("jockey_claim_lbs"),
                trainer=runner.get("trainer"),
                trainer_id=runner.get("trainer_id"),
                owner=runner.get("owner"),
                owner_id=runner.get("owner_id"),
                comment=runner.get("comment"),
                raw_data=runner
            )
            db.add(result)
        
        # Also store the overall race result data
        race_result = RaceResult(
            race_id=race_id,
            date=race_data.get("date"),
            course=race_data.get("course"),
            course_id=race_data.get("course_id"),
            off_time=race_data.get("off"),
            race_name=race_data.get("race_name"),
            race_type=race_data.get("type"),
            race_class=race_data.get("class"),
            pattern=race_data.get("pattern"),
            rating_band=race_data.get("rating_band"),
            age_band=race_data.get("age_band"),
            distance=race_data.get("dist"),
            going=race_data.get("going"),
            surface=race_data.get("surface"),
            winning_time=race_data.get("winning_time_detail"),
            comments=race_data.get("comments"),
            raw_data=race_data
        )
        db.merge(race_result)
        
        db.commit()


class RaceResult(Base):
    """Stores overall race result information"""
    __tablename__ = "race_results"
    
    id = Column(Integer, primary_key=True, index=True)
    race_id = Column(String, ForeignKey("racecards.race_id"), unique=True, index=True)
    date = Column(String)
    course = Column(String)
    course_id = Column(String)
    off_time = Column(String)
    race_name = Column(String)
    race_type = Column(String)
    race_class = Column(String)
    pattern = Column(String)
    rating_band = Column(String)
    age_band = Column(String)
    distance = Column(String)
    going = Column(String)
    surface = Column(String)
    winning_time = Column(String)
    comments = Column(String)
    raw_data = Column(JSON)
    
    # Use string reference instead of direct class reference
    race = relationship("RaceCard", foreign_keys=[race_id], 
                        backref=backref("race_result", uselist=False))