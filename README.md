# University Student Support Assistant

A self-hosted LLM application that helps students with questions about
course registration, examination rules, library services, ICT support,
hostel applications, fee payment, the academic calendar, and student
conduct.

**Pipeline:** Browser frontend (HTML/CSS/JS) → FastAPI backend → local
LLM served by **Ollama**. A small built-in FAQ knowledge base gives the
model extra grounding before it answers (bonus feature).

```
student-support-llm/
├── backend/
│   ├── __init__.py
│   ├── main.py          FastAPI app: /health, /ask routes, logging, errors
│   ├── llm_client.py     Talks to Ollama's HTTP API
│   ├── config.py         All settings (model name, URLs, prompt, logging)
│   ├── faq.py             Bonus: keyword-based FAQ lookup ("simple RAG")
│   └── logs/app.log      Created automatically at runtime
├── frontend/
│   ├── index.html
│   ├── style.css
│   └── app.js
├── tests/
│   └── test_api.py
├── requirements.txt
└── README.md
```

---

## 1. Prerequisites

- Python 3.10+
- [Ollama](https://ollama.com) installed
- A code editor (VS Code recommended)

---

## 2. Step-by-step setup and integration

### Step 1 — Install and start Ollama, pull a model

```bash
# Install Ollama from https://ollama.com (one-time)

# Pull a small, fast local model
ollama pull llama3.2:1b

# Start the Ollama server (keep this terminal open)
ollama serve
```

Verify it's working in a second terminal:

```bash
curl http://localhost:11434/api/generate -d '{"model":"llama3.2:1b","prompt":"Hello","stream":false}'
```

You should get back a JSON object with a `"response"` field. This
confirms the bottom layer of the pipeline (the LLM) is alive **before**
you build anything on top of it.

### Step 2 — Create and activate a virtual environment

```bash
cd student-support-llm
python -m venv venv

# Windows
venv\Scripts\activate

# macOS / Linux
source venv/bin/activate
```

### Step 3 — Install backend dependencies

```bash
pip install -r requirements.txt
```

### Step 4 — Configure the backend (optional)

`backend/config.py` reads settings from environment variables, with
sensible defaults already pointing at `http://localhost:11434` and
`llama3.2:1b`. If you pulled a different model, set:

```bash
# Windows (PowerShell)
$env:OLLAMA_MODEL="phi3"

# macOS / Linux
export OLLAMA_MODEL="phi3"
```

### Step 5 — Run the FastAPI backend

From the project root (with the venv active):

```bash
uvicorn backend.main:app --reload --port 8000
```

This is the **glue** of the pipeline: it exposes HTTP endpoints that
the frontend calls, and internally calls Ollama on the frontend's
behalf so the browser never talks to the LLM directly.

Check it's running:

- `http://localhost:8000/` → root message
- `http://localhost:8000/health` → `{"status": "ok", ...}`
- `http://localhost:8000/docs` → interactive Swagger UI, where you can
  test `/ask` directly from the browser without the frontend at all

### Step 6 — Open the frontend

The frontend is plain HTML/CSS/JS, so it doesn't need a build step.
Open `frontend/index.html` directly in a browser, **or** serve it so
it behaves like a real deployed site:

```bash
cd frontend
python -m http.server 5500
```

Then visit `http://localhost:5500`.

`frontend/app.js` has one important line near the top:

```javascript
const API_BASE_URL = "http://localhost:8000";
```

This is **the integration point**: it tells the browser-based frontend
exactly where the FastAPI backend lives. If you ever deploy the
backend somewhere else (a server, a Docker container, a cloud VM),
this is the only line you need to change.

### Step 7 — Use it

1. Type a question (or click a topic in the sidebar to auto-fill one).
2. Press **Enter** or click **Ask**.
3. The status dot in the top-right turns green when the backend is
   reachable, and red when it isn't.

---

## 3. How the pieces talk to each other (the actual pipeline)

```
Browser (index.html + app.js)
   │  fetch("http://localhost:8000/ask", { question })
   ▼
FastAPI backend (main.py)
   │  validates the question (rejects empty input -> 422)
   │  looks up FAQ context (faq.py)
   │  calls ask_llm(question, faq_context)  -->  llm_client.py
   ▼
llm_client.py
   │  POST http://localhost:11434/api/generate
   ▼
Ollama (running the local model, e.g. llama3.2:1b)
   │  returns generated text
   ▲
llm_client.py  -->  main.py  -->  JSON response { answer, faq_topic, response_time_seconds }
   ▲
Browser renders the answer as a new chat bubble
```

Logging happens inside `main.py` on every request: the question, the
generated answer, the FAQ topic matched (if any), response time, and
any errors are all written to `backend/logs/app.log` with a timestamp.

---

## 4. Error handling reference (Task 7)

| Situation                                 | What happens                                                                                                                                                                                  |
| ----------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Backend not running                       | `app.js` health check fails every 15s; status dot turns red and a banner reads "Could not reach the backend server."                                                                          |
| Model not running (Ollama down)           | `llm_client.py` raises `LLMConnectionError`; backend returns HTTP 503 with a clear message; frontend shows it as a system bubble                                                              |
| Ollama running but model missing/erroring | `llm_client.py` raises `LLMResponseError`; backend returns HTTP 502                                                                                                                           |
| Empty question                            | Caught client-side before the request is even sent (`inputHint` message); also caught server-side via Pydantic validation (`field_validator`) returning HTTP 422 as a second layer of defense |
| Slow response                             | Loading bubble with an animated "thinking…" indicator; after 4 seconds the message updates to reassure the student the model is still working                                                 |

---

## 5. Running the tests (Task 5)

With the backend dependencies installed and (ideally) Ollama running:

```bash
pytest tests/test_api.py -v
```

The tests check the `/health` endpoint, input validation on `/ask`,
and (when Ollama is available) that `/ask` returns a real answer and
correctly matches FAQ topics.

---

## 6. Bonus feature implemented: Simple FAQ-based grounding

`backend/faq.py` contains a small built-in University FAQ "knowledge
base" (8 topics matching the use case). Before each question is sent
to the LLM, the backend scores the question against each FAQ entry's
keywords and, if there's a match, injects that entry's factual answer
into the prompt as extra context. This is a simplified version of
retrieval-augmented generation (RAG): it keeps answers grounded in
real (if fictional, for this assignment) university policy instead of
relying purely on what the small local model already "knows." The
matched topic is also shown in the UI as an "FAQ match" tag so it's
easy to see when grounding kicked in.

---

## 7. Notes on production readiness

This project is a **prototype**, not a production deployment. Before
real deployment you would need, at minimum: HTTPS, authentication,
rate limiting, input sanitisation against prompt injection, a
production-grade ASGI setup (e.g. Gunicorn + Uvicorn workers behind a
reverse proxy), centralised structured logging/monitoring, and a
review of what student data is logged and how long it's retained.
These points are expanded on in the technical report's "Production
Readiness Discussion" section.
