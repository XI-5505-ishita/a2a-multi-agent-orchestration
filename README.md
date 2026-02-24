# A2A Multi-Agent Orchestration System

A production-style Agent-to-Agent (A2A) orchestration architecture built using FastAPI, LangChain, LangGraph, and Langfuse.

This system demonstrates autonomous multi-agent collaboration where a Host Agent dynamically plans and executes tasks by calling independent sub-agents via API.

---

## 🚀 Overview

This project implements a distributed A2A architecture with:

- 🔹 Host (Orchestrator) Agent
- 🔹 Summarizer Agent
- 🔹 Translator Agent
- 🔹 Asynchronous Task Lifecycle Pattern
- 🔹 LLM-based Execution Planning
- 🔹 Observability with Langfuse
- 🔹 Microservice Architecture

The host agent uses an LLM to:
1. Analyze the user query
2. Generate a dynamic execution plan
3. Call sub-agents via API only
4. Chain outputs between agents
5. Return final result

---

## 🧠 Architecture

User Query  
     ↓  
Host Agent (LLM Planning)  
     ↓  
Execution Plan (JSON list)  
     ↓  
API Calls → Sub Agents  
     ↓  
Async Task Lifecycle (create-task + polling)  
     ↓  
Final Output  

Each sub-agent runs independently and exposes:

- `POST /create-task`
- `GET /task/{task_id}`
- `GET /agent-card`

---

## 🏗 Project Structure

```
a2aSystem/
│
├── orchestrator_agent/
│   ├── main.py
│   ├── app.py
│   └── client.py
│
├── summarizer_agent/
│   ├── app.py
│   └── graph.py
│
├── translator_agent/
│   ├── app.py
│   └── graph.py
│
├── shared/
│   ├── schema.py
│   └── task_store.py
│
├── requirements.txt
└── .gitignore
```

---

## ⚙️ Technologies Used

- **FastAPI** — Microservice APIs  
- **LangChain** — LLM interaction  
- **LangGraph** — Agent logic workflow  
- **Langfuse** — LLM observability & tracing  
- **OpenAI GPT-4o-mini** — Reasoning model  
- **HTTPX** — Async API calls  
- **Python 3.10+**

---

## 🔄 A2A Task Lifecycle Pattern

Sub-agents follow an asynchronous lifecycle:

1. Host calls `/create-task`
2. Agent returns `task_id`
3. Host polls `/task/{task_id}`
4. Agent updates status → `completed`
5. Host retrieves final result

This pattern allows:

- Background processing
- Scalability
- Decoupled execution
- Future distributed expansion

---

## 🧠 Autonomous Planning Example

Example query:

Summarize this paragraph and then translate the summary into Hindi.

Generated execution plan:

```json
["SummarizerAgent", "TranslatorAgent"]
```

The host dynamically generates the plan using LLM reasoning — no hardcoded routing logic.

---

## 📊 Observability (Langfuse)

The system integrates Langfuse to track:

- Execution traces
- Planning steps
- Agent calls
- LLM prompts & outputs
- Token usage & cost
- Latency

Each multi-step query produces a full execution trace.

---

## 🔧 Setup Instructions

### 1️⃣ Clone Repository

```bash
git clone https://github.com/YOUR_USERNAME/a2a-multi-agent-orchestration.git
cd a2aSystem
```

### 2️⃣ Create Virtual Environment

```bash
python -m venv venv
venv\Scripts\activate   # Windows
```

### 3️⃣ Install Dependencies

```bash
pip install -r requirements.txt
```

### 4️⃣ Create `.env` File

In root directory:

```
OPENAI_API_KEY=your_openai_key
LANGFUSE_PUBLIC_KEY=your_langfuse_public_key
LANGFUSE_SECRET_KEY=your_langfuse_secret_key
LANGFUSE_HOST=https://cloud.langfuse.com
```

---

## ▶️ Running the System

### Start Summarizer Agent

```bash
uvicorn summarizer_agent.app:app --port 8101
```

### Start Translator Agent

```bash
uvicorn translator_agent.app:app --port 8102
```

### Run Host Agent

```bash
python orchestrator_agent/main.py
```

---

## 🧪 Example Multi-Step Query

Summarize this paragraph. Then translate the summary into Hindi. Finally, summarize the Hindi output again.

Expected execution plan:

```json
["SummarizerAgent", "TranslatorAgent", "SummarizerAgent"]
```

---

## 🔮 Future Improvements

- Replace in-memory `task_store` with Redis
- Add dynamic agent discovery
- Add parallel execution
- Implement distributed tracing across services
- Add reflection / retry loop inside agents
- Add confidence scoring

---

## 📌 Key Concepts Demonstrated

- Agent-to-Agent Protocol
- API-based agent communication
- Async task orchestration
- LLM-based execution planning
- Microservice design
- Observability-driven debugging

---

