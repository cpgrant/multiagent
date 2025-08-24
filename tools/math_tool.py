# tools/math_tool.py

def run(a: float, b: float):
    # registry route for addition
    return a + b

def math(op: str, a: float, b: float):
    if op == "add":
        return a + b
    if op == "sub":
        return a - b
    if op == "mul":
        return a * b
    if op == "div":
        if b == 0:
            raise ZeroDivisionError("Division by zero")
        return a / b
    raise ValueError(f"Unknown math op: {op}")