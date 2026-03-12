from sqlalchemy import Column, Integer, String, Text, DateTime
from datetime import datetime
from app.database import Base

class AICache(Base):
    __tablename__ = "ai_cache"

    id = Column(Integer, primary_key=True, index=True)
    question_hash = Column(String(64), index=True) # Hash of (role + question)
    answer = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
