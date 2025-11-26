import os
import json
import re
from fastapi import FastAPI, HTTPException
from dotenv import load_dotenv
from fastapi.middleware.cors import CORSMiddleware
from google import genai

from app.db import engine, SessionLocal
from app.models import Base, Goal
from app.schemas import GoalIn, GoalOut

load_dotenv()
genai_client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

app = FastAPI()

origins = ["http://localhost:3000"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Startup event to create tables only ---
@app.on_event("startup")
async def startup():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


# --- Prompt builder ---
def build_prompt(goal: str):
    """
    Prompt AI to return tasks and a dynamic complexity (1-10)
    """
    return f"""
Generate EXACT JSON output:

{{
  "tasks": [
    {{"title": "...", "description": "...", "estimated_minutes": 5}},
    ... exactly 5 items
  ],
  "complexity": "Provide a number from 1 (easy) to 10 (hard) based on the goal complexity"
}}

Goal: "{goal}"
"""


# --- Call Gemini API ---
async def call_gemini(prompt: str) -> dict:
    resp = genai_client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt
    )
    text = resp.text

    # Try JSON parsing
    try:
        return json.loads(text)
    except:
        # Extract JSON from any extra text
        match = re.search(r"(\{.*\})", text, re.S)
        if not match:
            raise HTTPException(status_code=500, detail="Failed to parse AI response")
        return json.loads(match.group(1))


# --- API endpoint ---
@app.post("/api/goals", response_model=GoalOut)
async def create_goal(payload: GoalIn):
    # Call AI to generate tasks and complexity
    parsed = await call_gemini(build_prompt(payload.goal))

    # Validate parsed response
    tasks = parsed.get("tasks")
    complexity = parsed.get("complexity")

    if not tasks or complexity is None:
        raise HTTPException(status_code=500, detail="Invalid response from AI")

    # Save in database
    async with SessionLocal() as session:
        g = Goal(
            goal_text=payload.goal,
            tasks=tasks,
            complexity=int(complexity),  # Ensure it's numeric
        )
        session.add(g)
        await session.commit()
        await session.refresh(g)
        return g
