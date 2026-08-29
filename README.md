# Sentry

Sales CRM agent — TODO: one-line description.

## Setup

### Backend (FastAPI + LangGraph)

```bash
cd backend
# TODO: create and activate a virtualenv
pip install -r requirements.txt
cp .env.example .env  # fill in OPENAI_API_KEY or ANTHROPIC_API_KEY
uvicorn main:app --reload
```

Deploys to Render. TODO: add Render deployment instructions/config.

### Frontend (Next.js)

```bash
cd frontend
npm install
cp .env.local.example .env.local
npm run dev
```

Deploys to Vercel. TODO: add Vercel deployment instructions/config.
