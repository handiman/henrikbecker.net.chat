from typing import Any, Literal

from fastapi import APIRouter, Depends, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ValidationError

from api.rate_limit import rate_limit

router = APIRouter()
METHODS = {}


def method(name: str):
    def register(func):
        METHODS[name] = func
        return func

    return register


@method("tools/list")
async def handle_tools_list(params: dict) -> dict:
    return {"tools": []}


class MCPRequest(BaseModel):
    jsonrpc: Literal["2.0"]
    id: str
    method: str
    params: dict[str, Any] = {}  # noqa: F821


def rpc_error(id: str | int | None, code: int, message: str) -> JSONResponse:
    return JSONResponse({"jsonrpc": "2.0", "id": id, "error": {"code": code, "message": message}})


def rpc_invalid_request() -> JSONResponse:
    return rpc_error(None, -32600, "Invalid Request")


def rpc_method_not_found(id: str) -> JSONResponse:
    return rpc_error(id, -32601, "Method not found")


@router.post("/mcp", dependencies=[Depends(rate_limit)])
async def mcp(request: Request) -> JSONResponse:
    try:
        payload = MCPRequest.model_validate(await request.json())
    except (ValueError, ValidationError):
        return rpc_invalid_request()
    method = METHODS.get(payload.method)
    if method is None:
        return rpc_method_not_found(payload.id)
    result = await method(payload.params)
    return JSONResponse({"jsonrpc": "2.0", "id": payload.id, "result": result})
