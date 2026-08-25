# Capstone Project: Multi-Agent AI Assistant

A multi-agent chatbot that reads your request, picks the right agent, uses
external tools, and remembers the conversation — built with **Groq**,
**LangChain**, **LangGraph**, **LangSmith**, **FastAPI** and **Streamlit**.

Live demo: https://agentic-ai-e9t5lyk4inmwwdeefurkbk.streamlit.app

## Agents

| Agent | Handles | Tools |
|---|---|---|
| Research Agent | Web search, news, Wikipedia, weather | DuckDuckGo, Wikipedia, OpenWeatherMap |
| Python Agent | Calculations, code, math | Python REPL |
| Personal Assistant Agent | Email, Google Drive | Gmail (read/send), Google Drive (list/upload) |

A router looks at your message and sends it to the right agent. All three
agents share the same conversation memory (`thread_id`), so follow-up
questions work no matter which agent answered first.

## Project layout

This folder is its own separate GitHub repo (`Henry-141001/Agentic-AI`) -
it's deliberately kept apart from the rest of the day-by-day lessons.

```
backend/          FastAPI + LangGraph app
  tools.py          all the tools (search, wikipedia, weather, python, gmail, drive)
  agents.py          the 3 agents + the Groq LLM + LangSmith tracing setup
  main.py             LangGraph graph, router, memory, /chat endpoint
  oauth.py            Google login routes: /auth/login, /auth/callback
  .env                API keys (already set up, never commit this)
  requirements.txt
  Dockerfile
frontend/         Streamlit chat UI
  app.py
  .env                points the UI at the backend (localhost by default)
  requirements.txt
  Dockerfile
```

## Connecting Gmail/Drive (Personal Assistant Agent)

Unlike a typical "sign in with Google" desktop popup, this uses the
**web-based** Google login, so it works both locally and once deployed -
same setup either way.

**One-time setup, in Google Cloud Console:**
1. **APIs & Services → Credentials → Create Credentials → OAuth client ID**
2. Application type: **Web application** (not Desktop app)
3. Under **Authorized redirect URIs**, add both:
   - `http://localhost:8000/auth/callback` (for local testing)
   - `https://your-backend-name.onrender.com/auth/callback` (for the live
     deployed backend, once you have that URL from the Render step below)
4. Create it, then copy the **Client ID** and **Client secret** shown.
5. Add them to `backend/.env`:
   ```
   GOOGLE_CLIENT_ID=your-client-id
   GOOGLE_CLIENT_SECRET=your-client-secret
   BACKEND_PUBLIC_URL=http://localhost:8000
   ```
   (On Render, set the same two keys, but `BACKEND_PUBLIC_URL` should be
   your actual Render URL instead of localhost — see Deploying below.)

**To connect your account:** open `{your backend URL}/auth/login` in a
browser (there's also a "Connect Google Account" button in the Streamlit
sidebar) and approve access. You'll land on a plain "Google account
connected" page — go back to the chat and try a Gmail/Drive message.

**Good to know:** the connection is kept in memory, not saved to disk, so
by default it's lost whenever the backend restarts (a new deploy, or
Render's free tier waking up after being idle) - you'd need to click
"Connect Google Account" again each time.

**To avoid re-logging in constantly:** after connecting once, the success
page shows a `GOOGLE_REFRESH_TOKEN` value. Copy it and add it as an
environment variable in Render (see the Deploying table below). On every
future restart, the server will use it to reconnect automatically -
no browser login needed. This lasts about **7 days** at a time (a Google
limit for apps that haven't gone through their full verification process,
which isn't worth doing for a capstone project) - after that, one more
manual login via "Connect Google Account" refreshes it for another 7 days.

## Run it locally

Open **two terminals**.

**Terminal 1 — backend:**

```bash
cd backend
uv run uvicorn main:app --reload
```

The server starts immediately — Research and Python agents work right
away. Personal Assistant Agent tools only appear after you've connected
Google (see above).

**Terminal 2 — frontend:**

```bash
cd frontend
uv run streamlit run app.py
```

Streamlit opens in your browser. Try:
- "What's the weather in Kuala Lumpur?" → Research Agent
- "Calculate 15% of 240" → Python Agent
- "Summarize my latest emails" → Personal Assistant Agent (after connecting Google)

Click **New Chat** in the sidebar to start a fresh conversation (new memory
thread).

## LangSmith tracing

`agents.py` turns on tracing automatically as long as `LANGCHAIN_API_KEY` is
present in `backend/.env` (it already is). Open
https://smith.langchain.com and pick the **Multi-Agent AI Assistant**
project to watch every LLM call, routing decision, and tool call.

## Deploying

**Backend → Render**
1. Push this repo to GitHub (`.gitignore` already excludes `.env`, so your
   secrets stay local).
2. On Render: New → Web Service → connect the repo → set **Root Directory**
   to `backend` → **Branch: `master`** (Render will use the `Dockerfile`
   automatically).
3. Add these environment variables in Render's dashboard:

   | Key | Value |
   |---|---|
   | `GROQ_API_KEY` | (from your local `backend/.env`) |
   | `OPENWEATHER_API_KEY` | (from your local `backend/.env`) |
   | `LANGCHAIN_API_KEY` | (from your local `backend/.env`) |
   | `LANGCHAIN_TRACING_V2` | `true` |
   | `LANGCHAIN_PROJECT` | `Multi-Agent AI Assistant` |
   | `GOOGLE_CLIENT_ID` | (from Google Cloud Console) |
   | `GOOGLE_CLIENT_SECRET` | (from Google Cloud Console) |
   | `BACKEND_PUBLIC_URL` | your Render URL, e.g. `https://agentic-ai-ek7w.onrender.com` |
   | `PORT` | `10000` |
   | `GOOGLE_REFRESH_TOKEN` | *(optional, add after your first login - see "Connecting Gmail/Drive" above)* |

4. Once deployed, copy the Render URL and make sure it's added as an
   **Authorized redirect URI** (as `{url}/auth/callback`) back in Google
   Cloud Console — see "Connecting Gmail/Drive" above.

**Frontend → Streamlit Community Cloud**
1. On https://share.streamlit.io: New app → pick the repo → **Branch:
   `master`** → set the main file to `frontend/app.py`.
2. In the app's Settings → Secrets, add:
   ```
   API_URL = "https://your-backend-name.onrender.com"
   ```
   (your Render backend's public URL, from the step above).

Render's free tier spins down after 15 minutes of no traffic — the first
request after a while asleep can take 30-60 seconds to wake back up. This
is normal, not a bug.
