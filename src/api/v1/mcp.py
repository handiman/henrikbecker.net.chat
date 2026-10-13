from fastapi import Depends, Request
from fastapi import APIRouter
from fastapi.responses import JSONResponse

from api.rate_limit import rate_limit


router = APIRouter()

@router.post("/mcp", dependencies=[Depends(rate_limit)])
async def mcp(request: Request) -> JSONResponse: 
    return JSONResponse("Dummy Response")