from sqlalchemy import Column, Integer, String, JSON
from app.models.base import Base

class Owner(Base):
    __tablename__ = "owners"
    
    id = Column(Integer, primary_key=True, index=True)
    owner_id = Column(String, unique=True, index=True)
    name = Column(String)
    raw_data = Column(JSON)

    @classmethod
    def upsert_from_api(cls, db, data: dict):
        for item in data.get("search_results", []):
            owner_id = item.get("id")
            if not owner_id:
                continue
            instance = db.query(cls).filter(cls.owner_id == owner_id).first()
            if not instance:
                instance = cls(owner_id=owner_id)
            instance.name = item.get("name")
            instance.raw_data = item
            db.merge(instance)
        db.commit()
