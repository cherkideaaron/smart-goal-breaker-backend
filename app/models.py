from sqlalchemy.orm import declarative_base
from sqlalchemy import Column, String, Integer, JSON, Text
from uuid import uuid4

Base = declarative_base()

class Goal(Base):
    __tablename__ = "goals"

    id = Column(String, primary_key=True, default=lambda: str(uuid4()))
    goal_text = Column(Text, nullable=False)
    tasks = Column(JSON, nullable=False)
    complexity = Column(Integer, nullable=False)
