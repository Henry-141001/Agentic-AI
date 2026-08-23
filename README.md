# Capstone Project: Multi-Agent AI Assistant

A multi-agent chatbot that reads your request, picks the right agent, uses
external tools, and remembers the conversation — built with **Groq**,
**LangChain**, **LangGraph**, **LangSmith**, **FastAPI** and **Streamlit**.

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

```
Day 15/
  backend/          FastAPI + LangGraph app
    tools.py         all the tools (search, wikipedia, weather, python, gmail, drive)
    agents.py         the 3 agents + the Groq LLM + LangSmith tracing setup
    main.py            LangGraph graph, router, memory, /chat endpoint
    credentials.json   Google OAuth client (already set up, do not commit)
    .env               API keys (already set up, do not commit)
    requirements.txt
    Dockerfile
  frontend/         Streamlit chat UI
    app.py
    .env               points the UI at the backend (localhost by default)
    requirements.txt
    Dockerfile
```

## Run it locally

Open **two terminals**.

**Terminal 1 — backend:**

```bash
cd "Day 15/backend"
uv run uvicorn main:app --reload
```

By default the Personal Assistant Agent (Gmail/Drive) is turned **off**, so
the server starts immediately and the Research + Python agents work right
away.

To turn Gmail/Drive on: open `backend/.env` and set
`ENABLE_PERSONAL_ASSISTANT=true`, then restart the backend. On that next
startup, two browser windows will pop up (one for Gmail, one for Drive) —
log in with your Google account and approve access. The server will
finish starting only after you approve both. After that, `token_gmail.json`
and `token_drive.json` are saved next to `main.py` so you won't be asked
again.

**Terminal 2 — frontend:**

```bash
cd "Day 15/frontend"
uv run streamlit run app.py
```

Streamlit opens in your browser. Try:
- "What's the weather in Kuala Lumpur?" → Research Agent
- "Calculate 15% of 240" → Python Agent
- "Summarize my latest emails" → Personal Assistant Agent

Click **New Chat** in the sidebar to start a fresh conversation (new memory
thread).

## LangSmith tracing

`agents.py` turns on tracing automatically as long as `LANGCHAIN_API_KEY` is
present in `backend/.env` (it already is). Open
https://smith.langchain.com and pick the **Multi-Agent AI Assistant**
project to watch every LLM call, routing decision, and tool call.

## Deploying

**Backend → Render**
1. Push this repo to GitHub (`.gitignore` already excludes `.env`,
   `credentials.json`, and the `token_*.json` files, so your secrets stay
   local).
2. On Render: New → Web Service → connect the repo → set **Root Directory**
   to `Day 15/backend` (Render will use the `Dockerfile` automatically).
3. Add `GROQ_API_KEY`, `OPENWEATHER_API_KEY`, `LANGCHAIN_API_KEY`,
   `LANGCHAIN_TRACING_V2`, `LANGCHAIN_PROJECT` as environment variables in
   Render's dashboard (copy the values from your local `backend/.env`).
4. Gmail/Drive need a one-time login; that's easiest to keep working
   locally only, or you upload a pre-authorized `token_gmail.json` /
   `token_drive.json` as Render "Secret Files".

**Frontend → Streamlit Community Cloud**
1. On https://share.streamlit.io: New app → pick the repo → set the main
   file to `Day 15/frontend/app.py`.
2. In the app's Settings → Secrets, add:
   ```
   API_URL = "https://your-backend-name.onrender.com"
   ```
   (your Render backend's public URL, from the step above).
