# agents/planner.py
from typing import List, Dict, Any
from core.state import new_step  # dict factory with a 'state' field
import json, os
from pydantic import BaseModel
from core.state import PlanStep

USE_OPENAI = bool(os.getenv("OPENAI_API_KEY"))

class PlanRequest(BaseModel):
    goal: str
    constraints: Dict[str, Any]

def _fallback_plan(goal: str, constraints: Dict[str, Any]) -> List[PlanStep]:
    # Simple, deterministic 3-step plan for offline use
    steps = [
        PlanStep(id="plan-1", description="Clarify the goal and define success criteria", acceptance="Has concrete criteria"),
        PlanStep(id="plan-2", description="Choose one tool to progress (echo or math) and propose inputs", acceptance="Inputs present"),
        PlanStep(id="plan-3", description="Execute chosen tool and summarize result", acceptance="Summary references result"),
    ]
    return steps

def make_plan(goal: str, constraints: Dict[str, Any], mem_ctx: Any = None) -> List[PlanStep]:
    if not USE_OPENAI:
        return _fallback_plan(goal, constraints)

    from openai import OpenAI
    client = OpenAI()
    sys = (
        "You are a Planner. Produce a small plan (3–6 steps). "
        "Each step: id, description, optional tool (echo.say or math.add), inputs, acceptance."
        "Output JSON list of steps."
    )
    user = f"Goal: {goal}\nConstraints: {json.dumps(constraints)}"
    resp = client.chat.completions.create(
        model=os.getenv("MODEL_PLANNER","gpt-4o-mini"),
        messages=[{"role":"system","content":sys},{"role":"user","content":user}],
        temperature=0.2
    )
    txt = resp.choices[0].message.content
    data = json.loads(txt)
    return [PlanStep(**s) for s in data]



def create_initial_plan(user_prompt: str) -> List[Dict[str, Any]]:
    return [
        new_step(
            id="plan-1",
            description="Clarify the goal and define success criteria",
            acceptance="Has concrete criteria",
        ),
        new_step(
            id="plan-2",
            description="Choose one tool to progress (echo or math) and propose inputs",
            acceptance="Inputs present",
        ),
        new_step(
            id="plan-3",
            description="Execute chosen tool and summarize result",
            acceptance="Summary references result",
        ),
    ]