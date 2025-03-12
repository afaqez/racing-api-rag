from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, JSON
from sqlalchemy.orm import relationship
from app.models.base import Base
from sqlalchemy.types import UserDefinedType


# Define a custom Vector type for pgvector
class Vector(UserDefinedType):
    def get_col_spec(self, **kw):
        return "vector(1536)"
    
    def bind_processor(self, dialect):
        def process(value):
            return value
        return process
    
    def result_processor(self, dialect, coltype):
        def process(value):
            return value
        return process

class RaceCardEmbedding(Base):
    __tablename__ = "racecard_embeddings"
    
    id = Column(Integer, primary_key=True, index=True)
    race_id = Column(String, ForeignKey("racecards.race_id"), unique=True, index=True)
    embedding = Column(Vector)  # OpenAI embeddings are 1536-dimensional
    last_updated = Column(DateTime)
    embedding_metadata = Column(JSON)  # Renamed from metadata to embedding_metadata
    
    race = relationship("RaceCard", backref="embedding")

class HorseEmbedding(Base):
    __tablename__ = "horse_embeddings"
    
    id = Column(Integer, primary_key=True, index=True)
    horse_id = Column(String, ForeignKey("horses.horse_id"), unique=True, index=True)
    embedding = Column(Vector)  # OpenAI embeddings are 1536-dimensional
    last_updated = Column(DateTime)
    embedding_metadata = Column(JSON)  # Renamed from metadata to embedding_metadata
    
    horse = relationship("Horse", backref="embedding")

class JockeyEmbedding(Base):
    __tablename__ = "jockey_embeddings"
    
    id = Column(Integer, primary_key=True, index=True)
    jockey_id = Column(String, ForeignKey("jockeys.jockey_id"), unique=True, index=True)
    embedding = Column(Vector)
    last_updated = Column(DateTime)
    embedding_metadata = Column(JSON)  # Renamed from metadata to embedding_metadata
    
    jockey = relationship("Jockey", backref="embedding")

class TrainerEmbedding(Base):
    __tablename__ = "trainer_embeddings"
    
    id = Column(Integer, primary_key=True, index=True)
    trainer_id = Column(String, ForeignKey("trainers.trainer_id"), unique=True, index=True)
    embedding = Column(Vector)
    last_updated = Column(DateTime)
    embedding_metadata = Column(JSON)  # Renamed from metadata to embedding_metadata
    
    trainer = relationship("Trainer", backref="embedding")

class CourseEmbedding(Base):
    __tablename__ = "course_embeddings"
    
    id = Column(Integer, primary_key=True, index=True)
    course_id = Column(String, ForeignKey("courses.course_id"), unique=True, index=True)
    embedding = Column(Vector)
    last_updated = Column(DateTime)
    embedding_metadata = Column(JSON)  # Renamed from metadata to embedding_metadata
    
    course = relationship("Course", backref="embedding")
