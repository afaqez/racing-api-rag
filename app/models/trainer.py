from sqlalchemy import Column, Integer, String, JSON
from app.models.base import Base


class Trainer(Base):
    __tablename__ = "trainers"
    
    id = Column(Integer, primary_key=True, index=True)
    trainer_id = Column(String, unique=True, index=True)
    name = Column(String)
    raw_data = Column(JSON)

    @classmethod
    def upsert_from_api(cls, db, data: dict):
        for item in data.get("search_results", []):
            trainer_id = item.get("id")
            if not trainer_id:
                continue
            instance = db.query(cls).filter(cls.trainer_id == trainer_id).first()
            if not instance:
                instance = cls(trainer_id=trainer_id)
            instance.name = item.get("name")
            instance.raw_data = item
            db.merge(instance)
        db.commit()
 