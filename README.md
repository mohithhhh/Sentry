# Sentry

An autonomous sales agent that reads a rep's deal threads, reconstructs
where each deal stands, and makes an explainable judgment call — confident,
ambiguous, or deprioritize — with a visible, inspectable reasoning trace for
every decision.

## Setup

### Backend (FastAPI + LangGraph)

```bash
cd backend
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
cp .env.example .env  # fill in GOOGLE_API_KEY
.venv/bin/uvicorn main:app --reload
```

Deploys to Render — see [DEPLOY.md](DEPLOY.md).

### Frontend (Next.js)

```bash
cd frontend
npm install
cp .env.local.example .env.local
npm run dev
```

Deploys to Vercel — see [DEPLOY.md](DEPLOY.md).

## Try it

1. Start both servers above.
2. Open `localhost:3000`, click **Load deals** — watch Sentry triage all 5
   synthetic deals live, one at a time.
3. Once the Loop Analytics deal shows **ambiguous**, click **Simulate a
   reply** — watch it reclassify to confident and draft a follow-up, live.
