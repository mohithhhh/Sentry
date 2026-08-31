"""
FastAPI application entrypoint for Sentry.

Responsible for:
- Creating the FastAPI app instance
- Wiring up CORS middleware
- Registering routers from `routes/`

No business logic lives here — this is composition only.
"""

import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from routes import deals

# The Vercel URL doesn't exist until the frontend is deployed, so it can't be
# hardcoded here — set EXTRA_ALLOWED_ORIGINS on Render once it's known (see
# DEPLOY.md) rather than editing this file and redeploying.
_DEFAULT_ORIGINS = ["http://localhost:3000"]
_extra_origins = [
    origin.strip()
    for origin in os.environ.get("EXTRA_ALLOWED_ORIGINS", "").split(",")
    if origin.strip()
]
ALLOWED_ORIGINS = _DEFAULT_ORIGINS + _extra_origins

app = FastAPI(title="Sentry", version="0.1.0")

# TODO: tighten CORS config (methods/headers) before production
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(deals.router)


@app.get("/health")
def health_check() -> dict[str, str]:
    """Basic liveness check.

    TODO: implement — currently returns a static placeholder.
    """
    return {"status": "ok"}
