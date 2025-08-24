# core/orchestrator.py
import importlib
from typing import Callable, Dict, Any, List

#from agents.planner import create_initial_plan
import agents.planner as planner
from agents.executor import run_step
from agents.critic import evaluate, summarize_trace
from agents import router

# -------------------------------------------------------------------
# Dynamic tool registry (keeps your existing design)
# -------------------------------------------------------------------
_TOOL_REGISTRY: Dict[str, str] = {
    "echo.say": "tools.echo:run",        # expects run(text=...)
    "math.add": "tools.math_tool:run",   # expects run(a=..., b=...)
}

def get_tool(name: str) -> Callable[..., Any]:
    if name not in _TOOL_REGISTRY:
        raise ValueError(f"Unknown tool: {name}")
    module_name, func_name = _TOOL_REGISTRY[name].split(":")
    mod = importlib.import_module(module_name)
    return getattr(mod, func_name)

# -------------------------------------------------------------------
# Adapter so agents/executor can call tools.math(**kw) / tools.echo(**kw)
# -------------------------------------------------------------------
# core/orchestrator.py (replace the whole ToolRegistry class)
class ToolRegistry:
    @staticmethod
    def math(**kw):
        """
        Delegate to tools.math_tool.math(op,a,b).
        For pure addition, we still support the dynamic registry route.
        """
        op = kw.get("op")
        a = kw.get("a")
        b = kw.get("b")

        # Fast path for add via dynamic registry (keeps your original design)
        if op == "add":
            fn = get_tool("math.add")  # -> tools.math_tool:run(a,b)
            return fn(a=a, b=b)

        # General path uses math_tool.math(...) which handles sub/mul/div and ZeroDivisionError
        from tools import math_tool
        if hasattr(math_tool, "math"):
            return math_tool.math(op=op, a=a, b=b)

        # As a last resort, implement inline
        if op == "sub":
            return (a - b)
        if op == "mul":
            return (a * b)
        if op == "div":
            if b == 0:
                raise ZeroDivisionError("Division by zero")
            return (a / b)

        raise ValueError(f"Unsupported math op: {op}")

    @staticmethod
    def echo(**kw):
        text = kw.get("text", "")
        fn = get_tool("echo.say")  # -> tools.echo:run(text=...)
        return fn(text=text)
    
# -------------------------------------------------------------------
# Orchestration entrypoint
# -------------------------------------------------------------------
def run(user_prompt: str) -> Dict[str, Any]:
    """
    Orchestrate planning -> execution -> evaluation -> trace summary.
    Returns a dict: { plan: [...], outcome: {...}, trace: "..." }
    """

    plan: List[Dict[str, Any]] = planner.create_initial_plan(user_prompt)

    # Execute plan sequentially (router kept for future branching)
    for step in plan:
        _dest = router.route(step)  # currently unused; placeholder
        run_step(step, plan, user_prompt, tools=ToolRegistry)

    outcome = evaluate(plan)
    trace = summarize_trace(plan)

    # JSON-friendly plan (enums -> strings)
    printable_plan: List[Dict[str, Any]] = []
    for s in plan:
        s_out = dict(s)
        st = s_out.get("state")
        s_out["state"] = getattr(st, "value", st)
        printable_plan.append(s_out)

    return {
        "plan": printable_plan,
        "outcome": outcome,
        "trace": trace,
    }