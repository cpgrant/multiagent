
# 🧩 Multi-Agent Scaffold (Planner → Executor → Critic)

A tiny, test-covered scaffold that turns **natural language instructions** into a **plan**, chooses the right **tool**, executes it, and **checks the result**.  
It’s like a baby AI agent: **plan → act → review**.

---

## ✨ Features
- **Planner** creates a 3-step plan:
  1. Clarify the goal  
  2. Choose a tool (`math` or `echo`)  
  3. Execute & summarize  
- **Executor** runs the chosen tool, with a **max-attempts guard** to avoid infinite retries  
- **Critic** verifies acceptance criteria (e.g. “summary must mention the result”)  
- **Orchestrator** ties everything together with a dynamic tool registry  
- **Tools**:  
  - `math` → supports add, subtract, multiply, divide (with divide-by-zero protection)  
  - `echo` → repeats your text back  

---

## 🧱 Project structure

.
├── agents/               # planner, executor, critic, router
├── core/                 # orchestrator, shared state
├── tools/                # echo + math tool implementations
├── tests/                # pytest suite
├── app.py                # CLI entrypoint
├── requirements.txt
└── README.md

---

## 🚀 Quickstart

### 1. Clone & install
```bash
git clone https://github.com/YOUR_USER/multiagent.git
cd multiagent
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

2. Run a prompt

python app.py "Please add 5 and 7"

Expected output (simplified):

Plan: [
  {"id": "plan-2", "tool": "math", "inputs": {"op": "add", "a": 5.0, "b": 7.0}},
  {"id": "plan-3", "result": {"tool_output": 12.0, "summary": "Computed 5.0 + 7.0 = 12.0. Summary: The result is 12.0."}}
]
Outcome: {"complete": true, "score": 1.0}
Trace summary: steps=3 done=3 status=complete


⸻

🧪 Run tests

pytest -q

All tests should pass:
	•	✅ Happy path: 5 + 7 = 12
	•	✅ Echo fallback
	•	✅ Division by zero handled as error
	•	✅ Max-attempts guard prevents infinite retries

⸻

🔧 Configuration
	•	Optional OpenAI reasoning in agents/executor.py if you set OPENAI_API_KEY in the environment.
	•	Defaults to offline mode with deterministic responses.
	•	Config values (like tool registry) can be moved to config/default.yaml.

⸻

🛠️ Extending
	1.	Add new tools in tools/ (e.g., search, files, code).
	2.	Register them in core/orchestrator.py under _TOOL_REGISTRY.
	3.	Teach the planner/executor to detect when to use them.
	4.	Add new pytest cases in tests/.

⸻

📜 License

MIT

⸻

👩‍💻 Contributing

See CONTRIBUTING.md.
Please open issues or PRs for ideas, improvements, or bug fixes.

⸻

🌟 Why this project?

It’s a simple playground for AI agent design.
Instead of jumping straight into big frameworks, you can learn how an agent:
	•	Breaks down a request into steps
	•	Selects and calls tools
	•	Handles errors
	•	Checks its own work

Great for teaching, learning, or hacking on your own AI ideas!

---
