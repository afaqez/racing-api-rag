# app/models/session.py
from sqlalchemy import Column, Integer, String, DateTime, Text
from app.models.base import Base
from datetime import datetime


class ChatSession(Base):
    __tablename__ = "chat_sessions"
    
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String, unique=True, index=True)
    user_id = Column(String, index=True)
    chat_history = Column(Text)  
    last_updated = Column(DateTime, default=datetime.utcnow)
