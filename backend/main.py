"""
FastAPI application entrypoint for Sentry.

Responsible for:
- Creating the FastAPI app instance
- Wiring up CORS middleware
- Registering routers from `routes/`

No business logic lives here — this is composition only.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from routes import deals

# TODO: pull allowed origins from environment/config instead of hardcoding
ALLOWED_ORIGINS = [
    "http://localhost:3000",
]

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
