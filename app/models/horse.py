from sqlalchemy import Column, Integer, String, JSON, DateTime
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class Horse(Base):
    __tablename__ = "horses"
    
    id = Column(Integer, primary_key=True, index=True)
    horse_id = Column(String, unique=True, index=True)
    name = Column(String, index=True)
    dob = Column(String)
    age = Column(String)
    sex = Column(String)
    sex_code = Column(String)
    colour = Column(String)
    colour_code = Column(String)
    region = Column(String)
    sire = Column(String)
    sire_id = Column(String, index=True)
    sire_region = Column(String)
    dam = Column(String)
    dam_id = Column(String, index=True)
    dam_region = Column(String)
    damsire = Column(String)
    damsire_id = Column(String, index=True)
    damsire_region = Column(String)
    breeder = Column(String)
    trainer = Column(String)
    trainer_id = Column(String, index=True)
    owner = Column(String)
    owner_id = Column(String, index=True)
    last_run = Column(String)
    form = Column(String)
    raw_data = Column(JSON)
    
    # Relationship is defined in the HorseResult model using backref
    
    @classmethod
    def upsert_from_api(cls, db, data: dict):
        """Upsert horse data from API response"""
        horse_id = None
        
        # Handle search results format
        if "search_results" in data:
            for item in data.get("search_results", []):
                horse_id = item.get("id")
                if not horse_id:
                    continue
                    
                instance = db.query(cls).filter(cls.horse_id == horse_id).first()
                if not instance:
                    instance = cls(horse_id=horse_id)
                    
                # Update basic fields from search results
                instance.name = item.get("name")
                instance.sire = item.get("sire")
                instance.dam = item.get("dam")
                
                # Only overwrite raw_data if we don't have more detailed data already
                if not instance.raw_data or len(instance.raw_data) < len(item):
                    instance.raw_data = item
                    
                db.merge(instance)
                
        # Handle horse pro API format
        elif "id" in data:
            horse_id = data.get("id")
            instance = db.query(cls).filter(cls.horse_id == horse_id).first()
            if not instance:
                instance = cls(horse_id=horse_id)
                
            # Update fields from horse pro API
            instance.name = data.get("name")
            instance.dob = data.get("dob")
            instance.sex = data.get("sex")
            instance.sex_code = data.get("sex_code")
            instance.colour = data.get("colour")
            instance.colour_code = data.get("colour_code")
            instance.breeder = data.get("breeder")
            instance.sire = data.get("sire")
            instance.sire_id = data.get("sire_id")
            instance.dam = data.get("dam")
            instance.dam_id = data.get("dam_id")
            instance.damsire = data.get("damsire")
            instance.damsire_id = data.get("damsire_id")
            
            # Only overwrite raw_data if we don't have more detailed data already
            if not instance.raw_data or len(instance.raw_data) < len(data):
                instance.raw_data = data
                
            db.merge(instance)
            
        # Handle racecard runner format - most comprehensive data source
        elif "horse_id" in data:
            horse_id = data.get("horse_id")
            instance = db.query(cls).filter(cls.horse_id == horse_id).first()
            if not instance:
                instance = cls(horse_id=horse_id)
            
            # Update all available fields from runner data
            instance.name = data.get("horse")
            instance.dob = data.get("dob")
            instance.age = data.get("age")
            instance.sex = data.get("sex")
            instance.sex_code = data.get("sex_code")
            instance.colour = data.get("colour")
            instance.region = data.get("region")
            
            # Sire information
            instance.sire = data.get("sire")
            instance.sire_id = data.get("sire_id")
            instance.sire_region = data.get("sire_region")
            
            # Dam information
            instance.dam = data.get("dam")
            instance.dam_id = data.get("dam_id")
            instance.dam_region = data.get("dam_region")
            
            # Damsire information
            instance.damsire = data.get("damsire")
            instance.damsire_id = data.get("damsire_id")
            instance.damsire_region = data.get("damsire_region")
            
            # Additional information
            instance.breeder = data.get("breeder")
            instance.trainer = data.get("trainer")
            instance.trainer_id = data.get("trainer_id")
            instance.owner = data.get("owner")
            instance.owner_id = data.get("owner_id")
            instance.last_run = data.get("last_run")
            instance.form = data.get("form")
            
            # Store the complete raw data
            instance.raw_data = data
            
            db.merge(instance)
        
        if horse_id:
            db.commit()
            return horse_id
        return None
