from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from workers import asgi

from api.rate_limit import rate_limit
from api.v1.hello import router as hello_router

ALLOWED_ORIGINS = [
    "https://henrikbecker.net",
    "https://www.henrikbecker.net",
    "https://becker-consulting.se",
    "https://www.becker-consulting.se",
]

app = FastAPI(title="henrikbecker API", docs_url=None, redoc_url=None, openapi_url=None)

# Added last = outermost, so CORS headers are also present on 429 responses.
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_methods=["GET", "OPTIONS"],
    allow_headers=["Content-Type"],
    max_age=86400,
)

app.include_router(hello_router, prefix="/api/v1", dependencies=[Depends(rate_limit)])

Default = asgi.entrypoint(app)
