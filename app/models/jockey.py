from sqlalchemy import Column, Integer, String, JSON
from app.models.base import Base


class Jockey(Base):
    __tablename__ = "jockeys"
    
    id = Column(Integer, primary_key=True, index=True)
    jockey_id = Column(String, unique=True, index=True)
    name = Column(String)
    raw_data = Column(JSON)

    @classmethod
    def upsert_from_api(cls, db, data: dict):
        for item in data.get("search_results", []):
            jockey_id = item.get("id")
            if not jockey_id:
                continue
            instance = db.query(cls).filter(cls.jockey_id == jockey_id).first()
            if not instance:
                instance = cls(jockey_id=jockey_id)
            instance.name = item.get("name")
            instance.raw_data = item
            db.merge(instance)
        db.commit()
