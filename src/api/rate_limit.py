from fastapi import HTTPException, Request


async def rate_limit(request: Request) -> None:
    """Reject the request with 429 if the client exceeds the RATE_LIMITER quota."""
    # Cloudflare sets CF-Connecting-IP; it cannot be spoofed by clients.
    key = request.headers.get("cf-connecting-ip") or "unknown"
    outcome = await request.scope["env"].RATE_LIMITER.limit(key=key)
    if not outcome.success:
        raise HTTPException(
            status_code=429,
            detail="Rate limit exceeded",
            headers={"Retry-After": "60"},
        )
