from collections.abc import Awaitable, Callable
from typing import Annotated, Any

from fastapi import APIRouter, Depends, Request, Response

AZURE_URL = "https://henrikbecker.azurewebsites.net"

# Headers that must not be copied to the upstream request.
_SKIPPED_REQUEST_HEADERS = {"host", "content-length", "connection", "transfer-encoding"}

router = APIRouter()

Fetch = Callable[..., Awaitable[Any]]


def get_fetch() -> Fetch:
    """The outbound fetch; a dependency so tests can replace it."""
    from workers import fetch  # only importable inside the Workers runtime

    return fetch


FetchDep = Annotated[Fetch, Depends(get_fetch)]


async def _forward(request: Request, path: str, fetch: Fetch) -> Response:
    headers = {
        k: v for k, v in request.headers.items() if k.lower() not in _SKIPPED_REQUEST_HEADERS
    }
    upstream = await fetch(
        f"{AZURE_URL}{path}",
        method="POST",
        headers=headers,
        body=await request.body(),
    )
    media_type = upstream.headers.get("content-type")
    return Response(
        content=await upstream.bytes(),
        status_code=upstream.status,
        media_type=media_type,
    )


@router.post("/ask/{collection}")
async def ask(collection: str, request: Request, fetch: FetchDep) -> Response:
    return await _forward(request, f"/ai/ask/{collection}", fetch)


@router.post("/ingest/{collection}")
@router.post("/ingress/{collection}", include_in_schema=False)
async def ingest(collection: str, request: Request, fetch: FetchDep) -> Response:
    return await _forward(request, f"/ai/ingest/{collection}", fetch)
