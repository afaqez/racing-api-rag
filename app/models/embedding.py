from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.types import UserDefinedType

Base = declarative_base()

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
    
    # No relationship needed since we're using raw SQL for table creation

class HorseEmbedding(Base):
    __tablename__ = "horse_embeddings"
    
    id = Column(Integer, primary_key=True, index=True)
    horse_id = Column(String, ForeignKey("horses.horse_id"), unique=True, index=True)
    embedding = Column(Vector)  # OpenAI embeddings are 1536-dimensional
    
    # No relationship needed since we're using raw SQL for table creation
