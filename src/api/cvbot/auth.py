import hmac
import logging

from fastapi import HTTPException, Request

logger = logging.getLogger(__name__)


def _unauthorized() -> HTTPException:
    return HTTPException(
        status_code=401, detail="Unauthorized", headers={"WWW-Authenticate": "Bearer"}
    )


async def require_ingest_token(request: Request) -> None:
    """Allow only `Authorization: Bearer <INGEST_TOKEN>`, compared in constant time."""
    expected = getattr(request.scope["env"], "INGEST_TOKEN", None)
    if not expected:
        logger.error("INGEST_TOKEN is not configured")
        raise _unauthorized()

    scheme, _, token = request.headers.get("authorization", "").partition(" ")
    if scheme.lower() != "bearer" or not hmac.compare_digest(
        token.strip().encode(), str(expected).encode()
    ):
        raise _unauthorized()
