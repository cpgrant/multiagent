# agents/executor.py
import os
import re
from typing import Any, Dict, List
from core.state import StepState

# Detect if we can call OpenAI (kept compatible with your original file)
USE_OPENAI = bool(os.getenv("OPENAI_API_KEY"))

# -----------------------------
# Optional LLM-assisted reasoning
# -----------------------------
def reason(step) -> Any:
    """
    Lightweight helper to produce a short thought/answer using OpenAI if available.
    Accepts either a dict-like step or an object with .description/.inputs.
    """
    # Support dict or object style access
    desc = step.get("description") if isinstance(step, dict) else getattr(step, "description", "")
    inputs = step.get("inputs") if isinstance(step, dict) else getattr(step, "inputs", {})

    text = f"Reasoning about: {desc}. Inputs: {inputs}"
    if not USE_OPENAI:
        # Offline deterministic response
        return {"thought": text, "answer": "Drafted without LLM (fallback)."}

    from openai import OpenAI
    client = OpenAI()
    sys = "You are a concise problem-solver. Provide one short paragraph."
    user = text
    resp = client.chat.completions.create(
        model=os.getenv("MODEL_EXECUTOR", "gpt-4o-mini"),
        messages=[{"role": "system", "content": sys}, {"role": "user", "content": user}],
        temperature=0.2,
    )
    return {"thought": text, "answer": resp.choices[0].message.content}


# -----------------------------
# --- Heuristics to infer math intent from the user's prompt ---
# -----------------------------

NUM_RE = re.compile(r"[-+]?\d*\.?\d+")

def _parse_math_from_prompt(prompt: str):
    """
    Return (op, a, b) where op in {add, sub, mul, div}, or None if not confident.
    Handles:
      - add/sum/plus
      - subtract/minus / "subtract X from Y" (Y - X)
      - multiply/times
      - divide/over / "divide X by Y" and symbol-based: x+y, x-y, x*y, x/y
    """
    text = prompt.lower()

    # Symbol-based first (exactly two numbers with an operator between them)
    m = re.search(r"([-+]?\d*\.?\d+)\s*([+\-*/x÷×])\s*([-+]?\d*\.?\d+)", text)
    if m:
        a, sym, b = float(m.group(1)), m.group(2), float(m.group(3))
        if sym in ["+",]:
            return ("add", a, b)
        if sym in ["-",]:
            return ("sub", a, b)
        if sym in ["*", "x", "×"]:
            return ("mul", a, b)
        if sym in ["/", "÷"]:
            return ("div", a, b)

    nums = [float(n) for n in NUM_RE.findall(text)]

    # ADD
    if any(w in text for w in ["add", "sum", "plus", "together", "total"]) and len(nums) >= 2:
        return ("add", nums[0], nums[1])

    m = re.search(r"add\s+([-+]?\d*\.?\d+)\s+(and|&|\+)\s+([-+]?\d*\.?\d+)", text)
    if m:
        return ("add", float(m.group(1)), float(m.group(3)))

    # SUBTRACT (note: "subtract X from Y" means Y - X)
    if ("subtract" in text or "minus" in text) and len(nums) >= 2:
        # prefer "subtract X from Y"
        m = re.search(r"subtract\s+([-+]?\d*\.?\d+)\s+from\s+([-+]?\d*\.?\d+)", text)
        if m:
            x, y = float(m.group(1)), float(m.group(2))
            return ("sub", y, x)
        # or "Y minus X"
        m = re.search(r"([-+]?\d*\.?\d+)\s+minus\s+([-+]?\d*\.?\d+)", text)
        if m:
            return ("sub", float(m.group(1)), float(m.group(2)))
        # fallback: first two numbers: a - b
        return ("sub", nums[0], nums[1])

    # MULTIPLY
    if any(w in text for w in ["multiply", "times"]) and len(nums) >= 2:
        m = re.search(r"(multiply|times)\s+([-+]?\d*\.?\d+)\s+(by\s+)?([-+]?\d*\.?\d+)", text)
        if m:
            a = float(m.group(2)); b = float(m.group(4))
            return ("mul", a, b)
        return ("mul", nums[0], nums[1])

    # DIVIDE
    if any(w in text for w in ["divide", "over"]) and len(nums) >= 2:
        m = re.search(r"(divide|over)\s+([-+]?\d*\.?\d+)\s+(by\s+)?([-+]?\d*\.?\d+)", text)
        if m:
            a = float(m.group(2)); b = float(m.group(4))
            return ("div", a, b)
        # "a over b"
        m = re.search(r"([-+]?\d*\.?\d+)\s+over\s+([-+]?\d*\.?\d+)", text)
        if m:
            return ("div", float(m.group(1)), float(m.group(2)))
        return ("div", nums[0], nums[1])

    return None


# -----------------------------
# Main step executor
# -----------------------------
def run_step(step: Dict[str, Any], plan: List[Dict[str, Any]], user_prompt: str, tools) -> None:
    """
    Execute a single plan step in-place.

    Args:
        step: current step dict (mutated)
        plan: full plan list (used by plan-3 to read plan-2 outputs)
        user_prompt: the original user instruction
        tools: registry exposing .math(**kw) and .echo(**kw)
    """

    # ---- Max attempts guard (placed at the very top) ----
    if step["attempts"] >= step.get("max_attempts", 2):
        step["state"] = StepState.FAILED
        step["result"] = (step.get("result") or {}) | {"error": "max_attempts reached"}
        step["done"] = False
        return

    sid = step.get("id")

    # ---------- PLAN-1: set criteria and mark done ----------
    if sid == "plan-1":
        step["state"] = StepState.RUNNING
        # Optional: consult the reasoner (never block on failure)
        try:
            step["reason"] = reason(step)
        except Exception:
            step["reason"] = {"thought": "reasoning-skip", "answer": "n/a"}

        step["criteria"] = {
            "must_summarize": True,
            "must_reference_result": True,
            "result_type": "numeric",
        }
        step["result"] = {"noted_goal": user_prompt.strip()}
        step["attempts"] += 1
        step["state"] = StepState.DONE
        step["done"] = True
        return

    # ---------- PLAN-2: choose tool + inputs ----------
    if sid == "plan-2":
        step["state"] = StepState.RUNNING
        choice = _parse_math_from_prompt(user_prompt)
        if choice:
            op, a, b = choice
            step["tool"] = "math"
            step["inputs"] = {"op": op, "a": a, "b": b}
            step["result"] = {"proposal": f"Use math(op={op}, a={a}, b={b})"}
        else:
            step["tool"] = "echo"
            step["inputs"] = {"text": user_prompt}
            step["result"] = {"proposal": "Use echo(text=<prompt>)"}
        step["attempts"] += 1
        step["state"] = StepState.DONE
        step["done"] = True
        return

    # ---------- PLAN-3: execute chosen tool + summarize ----------
    if sid == "plan-3":
        plan2 = next((s for s in plan if s.get("id") == "plan-2"), None)
        if not plan2 or not plan2.get("tool") or not plan2.get("inputs"):
            step["state"] = StepState.FAILED
            step["result"] = {"error": "No tool/inputs chosen in plan-2"}
            step["done"] = False
            return

        tool = plan2["tool"]
        inputs = plan2["inputs"]

        step["state"] = StepState.RUNNING
        try:
            if tool == "math":
                out = tools.math(**inputs)  # expects: op, a, b
                op, a, b = inputs["op"], inputs["a"], inputs["b"]
                if op == "add":
                    summary = f"Computed {a} + {b} = {out}. Summary: The result is {out}."
                else:
                    summary = f"Computed math({op}) -> {out}. Summary: The result is {out}."
                step["result"] = {"tool_output": out, "summary": summary}

            elif tool == "echo":
                out = tools.echo(**inputs)
                summary = f"Echoed text. Summary: {out}"
                step["result"] = {"tool_output": out, "summary": summary}

            else:
                raise ValueError(f"Unknown tool: {tool}")

            step["attempts"] += 1
            step["state"] = StepState.DONE
            step["done"] = True

        except Exception as e:
            step["state"] = StepState.FAILED
            step["result"] = {"error": str(e)}
            step["done"] = False
        return

    # ---------- Unknown step id: mark failed (defensive) ----------
    step["state"] = StepState.FAILED
    step["result"] = {"error": f"Unknown step id: {sid}"}
    step["done"] = False