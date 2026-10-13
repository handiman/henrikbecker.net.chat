from collections.abc import Awaitable, Callable

from fastapi import HTTPException, Request


def limit_by(binding: str) -> Callable[[Request], Awaitable[None]]:
    """Dependency that rejects the request with 429 if the client exceeds the `binding` quota."""

    async def dependency(request: Request) -> None:
        # Cloudflare sets CF-Connecting-IP; it cannot be spoofed by clients.
        key = request.headers.get("cf-connecting-ip") or "unknown"
        outcome = await getattr(request.scope["env"], binding).limit(key=key)
        if not outcome.success:
            raise HTTPException(
                status_code=429,
                detail="Rate limit exceeded",
                headers={"Retry-After": "60"},
            )

    return dependency


rate_limit = limit_by("RATE_LIMITER")
ask_rate_limit = limit_by("ASK_RATE_LIMITER")
