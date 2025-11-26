from pydantic import BaseModel
from typing import List, Dict

class GoalIn(BaseModel):
    goal: str

class GoalOut(BaseModel):
    id: str
    goal_text: str
    tasks: List[Dict]
    complexity: int

    class Config:
        from_attributes = True
