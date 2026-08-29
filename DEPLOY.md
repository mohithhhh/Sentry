# Deploying Sentry

Sentry is a two-part deploy: the FastAPI + LangGraph backend goes to **Render**
(as a persistent Web Service, not a serverless function — SSE streaming needs
a long-lived process), and the Next.js frontend goes to **Vercel**.

**The live demo runs entirely locally** (`localhost:8000` + `localhost:3000`).
The Render/Vercel deployment is only the "it's really deployed" link for
judges to check afterward — it removes network/cold-start risk from the
actual presentation. See the pre-demo checklist at the bottom.

## 1. Backend → Render

1. Push this repo to GitHub if it isn't already.
2. In the Render dashboard: **New → Web Service**, connect the repo.
3. Configure:
   | Setting | Value |
   |---|---|
   | Root Directory | `backend` |
   | Runtime | Python 3 |
   | Build Command | `pip install -r requirements.txt` |
   | Start Command | `uvicorn main:app --host 0.0.0.0 --port $PORT` |
   | Instance Type | Free (fine for a demo) |

   `$PORT` must stay a literal environment variable reference in the start
   command — Render assigns the port at runtime and injects it; hardcoding a
   port number (e.g. `--port 8000`) will make the service fail to bind.
4. Add environment variables (Render dashboard → Environment):
   | Key | Value |
   |---|---|
   | `GOOGLE_API_KEY` | your real Gemini key |
   | `EXTRA_ALLOWED_ORIGINS` | leave empty for now — see step 3 below |
5. Deploy. Once live, note the service URL (`https://sentry-backend-xxxx.onrender.com`).
6. Confirm it: `curl https://<your-render-url>/health` → `{"status":"ok"}`.

## 2. Frontend → Vercel

1. In the Vercel dashboard: **New Project**, import the repo.
2. Set **Root Directory** to `frontend` (Next.js is auto-detected from there).
3. Add an environment variable (Vercel dashboard → Settings → Environment Variables):
   | Key | Value |
   |---|---|
   | `NEXT_API_BASE` | your Render URL from step 1.5, e.g. `https://sentry-backend-xxxx.onrender.com` |

   **This will not actually reach the browser.** Next.js only inlines
   environment variables prefixed `NEXT_PUBLIC_` into client-side code;
   `frontend/app/lib/api.ts` runs in client components (`DealList`,
   `TraceFeed`, `page.tsx` are all `"use client"`) and reads this value at
   request time in the browser. With this name, that lookup is always
   `undefined`, and the app silently falls back to its hardcoded
   `http://localhost:8000` default — meaning the deployed Vercel site will
   try to call `localhost` from the visitor's own browser, not your Render
   backend. If you actually want the deployed frontend to reach the
   deployed backend, rename this back to `NEXT_PUBLIC_API_BASE` (in the
   Vercel env var above, `.env.local.example`, and the `API_BASE` line in
   `frontend/app/lib/api.ts`).
4. Deploy. Note the resulting Vercel URL (`https://sentry-<project>.vercel.app`).

## 3. Close the loop: point the backend's CORS at the real Vercel URL

Now that the Vercel URL exists, go back to Render → Environment and set:

```
EXTRA_ALLOWED_ORIGINS=https://sentry-<project>.vercel.app
```

(comma-separate if you ever need more than one origin). Save — Render
restarts the service automatically to pick it up. No code change or redeploy
needed; `backend/main.py` reads this at startup.

Confirm: open the deployed Vercel URL, open the browser console, click
**Load deals** — no CORS errors.

## Pre-demo checklist

- [ ] **Ping the Render URL a few minutes before presenting.** Render's free
      tier sleeps a service after 15 minutes of no traffic, and waking it
      back up takes ~30–60 seconds. Hit `https://<your-render-url>/health`
      from a browser tab shortly before you go on, so it's warm if a judge
      checks it live.
- [ ] **Confirm `GOOGLE_API_KEY` is actually set on Render**, separately from
      your local `.env` — they don't share state.
- [ ] **Run the actual demo against localhost, not Render.** Start the
      backend locally (`uvicorn main:app --reload`, port 8000) and the
      frontend locally (`npm run dev`, which defaults
      `NEXT_PUBLIC_API_BASE` to `http://localhost:8000`). This is the
      version you present from — it removes Render's cold-start and network
      latency from the moment the hero deal needs to reclassify live.
- [ ] **Treat the Vercel/Render pair purely as the "yes, this is really
      deployed" link** to hand judges afterward, not the thing you drive the
      live walkthrough from.
