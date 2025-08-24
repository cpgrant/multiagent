# agents/router.py
from typing import Dict, Any

def pick_tool(step, constraints: Dict[str, Any]) -> Dict[str, Any]:
    desc = (step.description or "").lower()
    # Very simple routing logic for demo
    if "sum" in desc or "add" in desc or step.tool == "math.add":
        return {"tool": "math.add", "reason": "Math keywords or pre-selected."}
    if "echo" in desc or step.tool == "echo.say":
        return {"tool": "echo.say", "reason": "Echo requested or safe default."}
    # Default: no tool (pure reasoning)
    return {"tool": "NO_TOOL", "reason": "No clear tool needed."}


def route(step: Dict[str, Any]) -> str:
    """
    Decide which component should handle the step.
    For now, always return 'executor' so core/orchestrator can proceed.
    """
    return "executor"