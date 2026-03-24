# StackHeal AI

An intelligent multi-agent debugging pipeline. Paste any code or error log and get back a root cause, a fix, and a plain-English explanation — powered by 7 Groq AI agents chained together behind a FastAPI backend and a React + TypeScript frontend.

---

## Architecture

```
┌──────────────────────────────────────────────┐
│   React + TypeScript  (Vite — port 5173)     │
│   App.tsx  →  POST /analyze                  │
└──────────────────────┬───────────────────────┘
                       │  Vite proxy (no CORS)
                       ▼
┌──────────────────────────────────────────────┐
│   FastAPI  (Uvicorn — port 8000)             │
│   main.py  →  orchestrator.py                │
└───┬──────────┬──────────┬────────────────────┘
    ▼          ▼          ▼
Agent 1     Agent 2    Agent 3        ...and 4 more
error_      error_     error_
detection   line       classify
```

### The 7 agents

| # | File | Job |
|---|------|-----|
| 1 | `error_detection.py` | Detects error type and message |
| 2 | `error_line.py` | Finds the failing line number and snippet |
| 3 | `error_classify.py` | Classifies severity and programming language |
| 4 | `root_cause.py` | Explains why the error happens |
| 5 | `fix.py` | Suggests the minimal corrected code |
| 6 | `explain.py` | Produces beginner and developer explanations |
| 7 | `confident.py` | Scores overall confidence (0 – 1) |

---

## Project Structure

```
stackheal/
├── backend/
│   ├── .env                 ← GROQ_API_KEY (never commit this)
│   ├── requirements.txt
│   ├── config.py            ← loads .env; all agents import key from here
│   ├── main.py              ← FastAPI server + all HTTP routes
│   ├── orchestrator.py      ← runs agents 1-7 in sequence
│   ├── error_detection.py
│   ├── error_line.py
│   ├── error_classify.py
│   ├── root_cause.py
│   ├── fix.py
│   ├── explain.py
│   └── confident.py
└── frontend/
    ├── index.html           ← Google Fonts included
    ├── package.json
    ├── tsconfig.json
    ├── vite.config.ts       ← proxy forwards /analyze to port 8000
    └── src/
        ├── main.tsx
        └── App.tsx
```

---

## Prerequisites

| Tool | Minimum version | Check |
|------|----------------|-------|
| Python | 3.10+ | `python --version` |
| Node.js | 18+ | `node --version` |
| npm | 9+ | `npm --version` |

You also need a **Groq API key** — get one free at https://console.groq.com

---

## Setup & Running

Open **two terminal windows** — one for the backend, one for the frontend.

---

### Terminal 1 — Backend

```bash
# 1. Go into the backend folder — this step is critical
cd stackheal/backend

# 2. Create a virtual environment
python -m venv venv

# 3. Activate it
#    Windows:
venv\Scripts\activate
#    Mac / Linux:
source venv/bin/activate

# You should now see (venv) at the start of your prompt.

# 4. Install dependencies
pip install -r requirements.txt

# 5. Add your Groq API key to .env
#    The file already exists — just confirm it contains:
#    GROQ_API_KEY=gsk_your_key_here
#    (no quotes, no spaces around the = sign)

# 6. Start the server
uvicorn main:app --reload --port 8000
```

**Expected output:**
```
[StackHeal] ✅ All 7 agents loaded successfully
INFO:     Uvicorn running on http://127.0.0.1:8000
```

**Verify it works** — open this in your browser:
```
http://localhost:8000/health
```
You should see `{"status":"ok","service":"StackHeal AI"}`.

Interactive API docs are at: `http://localhost:8000/docs`

---

### Terminal 2 — Frontend

```bash
# 1. Go into the frontend folder
cd stackheal/frontend

# 2. Install Node dependencies (only needed once)
npm install

# 3. Start the dev server
npm run dev
```

**Expected output:**
```
  VITE v5.x.x  ready in xxx ms
  ➜  Local:   http://localhost:5173/
```

Open `http://localhost:5173` — the StackHeal landing page will appear.

---

## How the Proxy Works

`vite.config.ts` contains:

```ts
proxy: {
  '/analyze': 'http://localhost:8000',
  '/health':  'http://localhost:8000',
  '/history': 'http://localhost:8000',
}
```

When the React app calls `/analyze`, Vite silently forwards it to FastAPI on your behalf. The browser sees it as a same-origin request — **CORS never triggers**. This is why `App.tsx` has `const API_BASE = ""`.

---

## API Reference

### `POST /analyze`

**Request body:**
```json
{
  "code": "your code or error log here",
  "language": "Python"
}
```

**Response:**
```json
{
  "type": "RuntimeError",
  "message": "cannot read property 'map' of undefined",
  "line": 22,
  "snippet": "user.profile.age",
  "severity": "High",
  "language": "JavaScript",
  "root_cause": "Object is null before method call",
  "description": "Add null check before accessing property",
  "correctedCode": "if (user && user.profile) { const data = user.profile.age; }",
  "simple": "Your code tried to use something that doesn't exist yet.",
  "detailed": "A TypeError is thrown at runtime when accessing a property on an undefined object.",
  "confidence": 0.91
}
```

### Other routes

| Method | Route | Description |
|--------|-------|-------------|
| GET | `/` | Service info |
| GET | `/health` | Health check |
| GET | `/docs` | Auto-generated Swagger UI |
| POST | `/analyze` | Run the full pipeline |
| POST | `/analyze/stream` | Same pipeline via Server-Sent Events |
| GET | `/history` | Last 20 analyses |
| DELETE | `/history` | Clear history |
| GET | `/history/{id}` | Single past result |

---

## Troubleshooting

**"Could not import module main" when running uvicorn**
You are in the wrong folder. You must `cd` into `stackheal/backend` first, then run uvicorn. Running it from the parent folder (`stackheal/`) will always fail.

**"GROQ_API_KEY is missing" on startup**
`backend/.env` is missing or empty. It must contain `GROQ_API_KEY=gsk_...` with no quotes.

**"ModuleNotFoundError: No module named 'groq'"**
You forgot to activate the virtual environment. Run `venv\Scripts\activate` (Windows) or `source venv/bin/activate` (Mac/Linux) before uvicorn.

**"Address already in use" on port 8000**
Something else is using that port. Use `--port 8001` instead, then update all three proxy targets in `vite.config.ts` to `8001` and restart `npm run dev`.

**Frontend shows "Pipeline Error — Failed to fetch"**
The backend is not running. Start uvicorn first, confirm `/health` responds, then use the UI.

**"node: command not found"**
Node.js is not installed. Download LTS from https://nodejs.org

**"vite: command not found"**
`npm install` was not run. Run it inside `stackheal/frontend/` first.

**Blank white page at localhost:5173**
Open browser DevTools (F12) → Console tab and share the error. Usually means `npm install` didn't complete cleanly — delete `node_modules/`, run `npm install` again.

**Agent cards all show "AgentError"**
Your Groq API key is invalid or expired. Get a new one at https://console.groq.com, paste it into `backend/.env`, restart uvicorn.

**Confidence score stuck at 50%**
Agent 7 failed silently — 0.5 is its fallback. Usually the same cause as above (bad API key).

**Code changes to agents not reflecting**
Stop uvicorn with `Ctrl+C` and restart it. The `--reload` flag sometimes misses changes to imported modules.

---

## Quick Reference

| | URL |
|-|-----|
| App UI | http://localhost:5173 |
| Backend root | http://localhost:8000 |
| Health check | http://localhost:8000/health |
| Swagger docs | http://localhost:8000/docs |
| History | http://localhost:8000/history |

---

## Security Notes (before going to production)

- Replace `allow_origins=["*"]` in `main.py` with your actual domain
- Never commit `.env` to Git — it is already in `.gitignore`
- Add rate limiting to `/analyze` (e.g. the `slowapi` package)
- Rotate the Groq API key if this repo is ever made public
