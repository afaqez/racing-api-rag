from sqlalchemy import Column, Integer, String, JSON
from app.models.base import Base


class Course(Base):
    __tablename__ = "courses"
    
    id = Column(Integer, primary_key=True, index=True)
    course_id = Column(String, unique=True, index=True)
    name = Column(String)
    region_codes = Column(JSON)  
    raw_data = Column(JSON)

    @classmethod
    def upsert_from_api(cls, db, data: dict):
        for item in data.get("courses", []):
            # Depending on the API response structure, adjust field names.
            course_id = item.get("course_id") or item.get("id") or item.get("name")
            if not course_id:
                continue
            instance = db.query(cls).filter(cls.course_id == course_id).first()
            if not instance:
                instance = cls(course_id=course_id)
            instance.name = item.get("name")
            instance.region_codes = item.get("region_codes")
            instance.raw_data = item
            db.merge(instance)
        db.commit()
