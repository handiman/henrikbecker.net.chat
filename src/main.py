from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from workers import asgi

from api.rate_limit import rate_limit
from api.v1.ai import router as ai_router
from api.v1.ping import router as ping_router

ALLOWED_ORIGINS = [
    "https://henrikbecker.net",
    "https://www.henrikbecker.net",
    "https://becker-consulting.se",
    "https://www.becker-consulting.se",
    "https://lena.fagervall.se",
    "https://lena-fagervall.github.io",
    "http://localhost:8787",
    "http://localhost:8080",
]

app = FastAPI(title="henrikbecker API", docs_url=None, redoc_url=None, openapi_url=None)

# Added last = outermost, so CORS headers are also present on 429 responses.
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Content-Type"],
    max_age=86400,
)

app.include_router(ping_router, prefix="/api/v1", dependencies=[Depends(rate_limit)])
# /ask and /ingest (used by the CV bot), with /ai/... as alias.
app.include_router(ai_router, dependencies=[Depends(rate_limit)])
app.include_router(
    ai_router, prefix="/ai", include_in_schema=False, dependencies=[Depends(rate_limit)]
)

Default = asgi.entrypoint(app)
