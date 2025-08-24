# tests/test_flow.py
import json
import importlib

def test_addition_happy_path():
    from core.orchestrator import run
    r = run("Please add 5 and 7")
    assert r["outcome"]["complete"] is True
    p2 = next(s for s in r["plan"] if s["id"] == "plan-2")
    p3 = next(s for s in r["plan"] if s["id"] == "plan-3")
    assert p2["tool"] == "math"
    assert p2["inputs"]["op"] == "add"
    assert p2["inputs"]["a"] in (5, 5.0) and p2["inputs"]["b"] in (7, 7.0)
    assert "tool_output" in p3["result"]
    assert str(p3["result"]["tool_output"]) in p3["result"]["summary"]
    # 5 + 7 = 12
    assert abs(float(p3["result"]["tool_output"]) - 12.0) < 1e-9

def test_echo_fallback():
    from core.orchestrator import run
    r = run("Please just repeat this sentence back")
    p2 = next(s for s in r["plan"] if s["id"] == "plan-2")
    p3 = next(s for s in r["plan"] if s["id"] == "plan-3")
    assert p2["tool"] == "echo"
    assert "Echoed text" in p3["result"]["summary"]
    assert r["outcome"]["complete"] is True  # echo path should still pass evaluator

def test_divide_by_zero_fails():
    from core.orchestrator import run
    r = run("Divide 10 by 0")
    p3 = next(s for s in r["plan"] if s["id"] == "plan-3")
    # division by zero should fail plan-3
    assert p3["state"] in ("failed", "FAILED") or str(p3["state"]).lower() == "failed"
    assert "error" in (p3["result"] or {})
    assert "zero" in p3["result"]["error"].lower()

def test_max_attempts_guard(monkeypatch):
    """
    Simulate the guard by making plan-3 already at max attempts before execution.
    We monkeypatch the planner to pre-fill attempts for plan-3.
    """
    import agents.planner as planner_mod
    from core.orchestrator import run

    orig_create_initial_plan = planner_mod.create_initial_plan

    def rigged_create_initial_plan(prompt: str):
        plan = orig_create_initial_plan(prompt)
        # set attempts to 2 for plan-3 (>= max_attempts=2)
        for s in plan:
            if s["id"] == "plan-3":
                s["attempts"] = s.get("max_attempts", 2)
        return plan

    monkeypatch.setattr(planner_mod, "create_initial_plan", rigged_create_initial_plan)

    r = run("Please add 5 and 7")
    p3 = next(s for s in r["plan"] if s["id"] == "plan-3")
    assert str(p3["state"]).lower() == "failed"
    assert "error" in (p3["result"] or {})
    assert "max_attempts" in p3["result"]["error"]