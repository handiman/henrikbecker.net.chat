import functools
import json
import logging
from collections.abc import Awaitable, Callable
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import JSONResponse

from api.cvbot.auth import require_ingest_token
from api.cvbot.llm import ask_llm
from api.cvbot.prompt import build_system_prompt
from api.cvbot.store import SUPPORTED_COLLECTIONS, CVStore
from api.rate_limit import ask_rate_limit

logger = logging.getLogger(__name__)

MAX_QUESTION_CHARS = 500
MAX_ASK_BODY_BYTES = 4096  # 500 characters can be up to 3000 bytes as JSON \uXXXX escapes
MAX_INGEST_BYTES = 100 * 1024  # the CV is about 30 KB

NO_DOCUMENT_ANSWER = "Sorry, I can't answer right now. Please try again in a little while."
FAILED_ANSWER = "My brain isn't answering right now. Please try again in a moment."

router = APIRouter()

AskLLM = Callable[[str, str], Awaitable[str]]


def get_store(request: Request) -> CVStore:
    return CVStore(request.scope["env"].CV_KV)


def get_ask_llm(request: Request) -> AskLLM:
    """The LLM call; a dependency so tests can replace it."""
    return functools.partial(ask_llm, request.scope["env"])


StoreDep = Annotated[CVStore, Depends(get_store)]
LLMDep = Annotated[AskLLM, Depends(get_ask_llm)]


def _check_collection(collection: str) -> None:
    if collection not in SUPPORTED_COLLECTIONS:
        raise HTTPException(status_code=404, detail="Not found")


async def _read_body(request: Request, max_bytes: int) -> bytes:
    declared = request.headers.get("content-length", "")
    if declared.isdigit() and int(declared) > max_bytes:
        raise HTTPException(status_code=413, detail="Request body too large")
    body = await request.body()
    if len(body) > max_bytes:
        raise HTTPException(status_code=413, detail="Request body too large")
    return body


async def _read_question(request: Request) -> str:
    body = await _read_body(request, MAX_ASK_BODY_BYTES)
    try:
        question = json.loads(body)
    except ValueError:
        question = None
    if not isinstance(question, str) or not question.strip():
        raise HTTPException(status_code=400, detail="Missing question")
    if len(question) > MAX_QUESTION_CHARS:
        raise HTTPException(status_code=413, detail="Question too long")
    return question


@router.post("/ask/{collection}", dependencies=[Depends(ask_rate_limit)])
async def ask(collection: str, request: Request, store: StoreDep, llm: LLMDep) -> JSONResponse:
    """Anonymous. The body is the question as a JSON string."""
    _check_collection(collection)
    question = await _read_question(request)
    try:
        document = await store.get(collection)
        if not document.strip():
            return JSONResponse({"answer": NO_DOCUMENT_ANSWER})
        answer = await llm(build_system_prompt(document), question)
        if not answer:
            raise ValueError("empty answer")
    except Exception as exc:
        # Log the type only: platform messages may carry internals; the question is visitor data.
        logger.error("CV bot failed to answer for %s: %s", collection, type(exc).__name__)
        return JSONResponse({"answer": FAILED_ANSWER, "error": True}, status_code=503)
    return JSONResponse({"answer": answer})


@router.post("/ingest/{collection}", dependencies=[Depends(require_ingest_token)])
@router.post(
    "/ingress/{collection}", include_in_schema=False, dependencies=[Depends(require_ingest_token)]
)
async def ingest(collection: str, request: Request, store: StoreDep) -> JSONResponse:
    """Bearer token required. The body is the whole CV document (Markdown or plain text)."""
    _check_collection(collection)
    body = await _read_body(request, MAX_INGEST_BYTES)
    try:
        document = body.decode("utf-8")
    except UnicodeDecodeError:
        raise HTTPException(status_code=400, detail="Document must be UTF-8") from None
    if not document.strip():
        raise HTTPException(status_code=400, detail="Missing document")
    try:
        await store.put(collection, document)
    except Exception as exc:
        logger.error("CV ingest failed for %s: %s", collection, type(exc).__name__)
        raise HTTPException(status_code=503, detail="Could not store the document") from None
    logger.info("Ingested CV document %s (%d characters)", collection, len(document))
    return JSONResponse("Document updated")
