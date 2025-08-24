# core/state.py
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

class StepState(str, Enum):
    PLANNED = "planned"
    RUNNING = "running"
    DONE = "done"
    FAILED = "failed"

# Optional: Pydantic models (you can keep these if you want them later)
class PlanStep(BaseModel):
    id: str
    description: str
    tool: Optional[str] = None
    inputs: Dict[str, Any] = Field(default_factory=dict)
    acceptance: Optional[str] = None
    attempts: int = 0
    max_attempts: int = 2
    done: bool = False
    result: Optional[Any] = None
    state: StepState = StepState.PLANNED
    # optional fields the executor may set
    reason: Optional[Dict[str, Any]] = None
    criteria: Optional[Dict[str, Any]] = None

class AgentState(BaseModel):
    task_id: str
    user_goal: str
    constraints: Dict[str, Any] = Field(default_factory=dict)
    plan: List[PlanStep] = Field(default_factory=list)
    evidence: List[Dict[str, Any]] = Field(default_factory=list)
    trace: List[Dict[str, Any]] = Field(default_factory=list)
    status: str = "initial"
    outcome: Optional[str] = None

def new_step(**kwargs) -> Dict[str, Any]:
    """
    Create a *dict-based* plan step with sane defaults; pass fields as kwargs to override.
    We use dicts for steps to match the current executor/orchestrator.
    """
    base: Dict[str, Any] = {
        "id": "",
        "description": "",
        "tool": None,
        "inputs": {},
        "acceptance": "",
        "attempts": 0,
        "max_attempts": 2,
        "done": False,
        "result": None,
        "state": StepState.PLANNED,
    }
    base.update(kwargs)
    return base