#!/usr/bin/env python3
# app.py
import sys
import json
from core.orchestrator import run  # orchestrates planner → executor → critic

def main():
    user_prompt = " ".join(sys.argv[1:]).strip()
    if not user_prompt:
        print('Usage: python app.py "Please add 5 and 7"')
        raise SystemExit(2)

    result = run(user_prompt)

    # result has: {"plan": [...], "outcome": {...}, "trace": "..."}
    print("Plan:", json.dumps(result["plan"], indent=2))
    print("Outcome:", json.dumps(result["outcome"]))
    print("Trace summary:", result["trace"])

if __name__ == "__main__":
    main()