from sqlalchemy import Column, Integer, String, DateTime
from pgvector.sqlalchemy import Vector
from datetime import datetime
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class RaceCardEmbedding(Base):
    __tablename__ = "racecard_embeddings"

    id = Column(Integer, primary_key=True, index=True)
    race_id = Column(String, unique=True, index=True)
    embedding = Column(Vector(1536))
    created_at = Column(DateTime, default=datetime.utcnow)
