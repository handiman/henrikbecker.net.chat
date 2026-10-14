from fastapi import Depends, FastAPI
from workers import asgi

from api.ai import router as ai_router
from api.cors import EnvCORSMiddleware
from api.mcp import router as mcp_router
from api.ping import router as ping_router
from api.rate_limit import rate_limit

ALLOWED_ORIGINS = [
    "https://henrikbecker.net",
    "https://www.henrikbecker.net",
    "https://becker-consulting.se",
    "https://www.becker-consulting.se",
]
# Only allowed when the ALLOW_LOCALHOST var is "true" (set it in .dev.vars, never in production).
DEV_ORIGINS = [
    "http://localhost:8787",
    "http://localhost:8080",
]

app = FastAPI(title="Henr API", redoc_url=None)

# Added last = outermost, so CORS headers are also present on 429 responses.
app.add_middleware(
    EnvCORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    dev_origins=DEV_ORIGINS,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Content-Type"],
    max_age=86400,
)

app.include_router(ping_router, dependencies=[Depends(rate_limit)])
app.include_router(mcp_router, dependencies=[Depends(rate_limit)])
# /ask and /ingest (used by the CV bot), with /ai/... as alias.
app.include_router(ai_router, dependencies=[Depends(rate_limit)])
app.include_router(
    ai_router, prefix="/ai", include_in_schema=False, dependencies=[Depends(rate_limit)]
)

Default = asgi.entrypoint(app)
