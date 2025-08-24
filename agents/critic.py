# agents/critic.py
from typing import List, Dict, Any
from core.state import StepState

def evaluate(plan: List[Dict[str, Any]]) -> Dict[str, Any]:
    all_pass = True
    for s in plan:
        acc = s.get("acceptance")
        if acc == "Has concrete criteria":
            all_pass &= bool(s.get("criteria"))
        elif acc == "Inputs present":
            all_pass &= bool(s.get("inputs"))
        elif acc == "Summary references result":
            res = s.get("result") or {}
            summary = res.get("summary", "")
            tool_out = res.get("tool_output")
            all_pass &= bool(summary) and (tool_out is not None) and (str(tool_out) in summary)
        # must be DONE
        all_pass &= (s.get("state") == StepState.DONE)
        all_pass &= (s.get("done") is True)
    return {"complete": all_pass, "score": 1.0 if all_pass else 0.0}

def summarize_trace(plan: List[Dict[str, Any]]) -> str:
    done_count = sum(1 for s in plan if s.get("state") == StepState.DONE)
    status = "complete" if done_count == len(plan) else "review"
    return f"steps={len(plan)} done={done_count} status={status}"