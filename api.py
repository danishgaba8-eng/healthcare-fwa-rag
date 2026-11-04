import logging
import os
from time import perf_counter
from uuid import uuid4
from fastapi import Request 
import os
import secrets
from pathlib import Path
from typing import Annotated

from dotenv import load_dotenv
from fastapi import Depends, FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from pydantic import BaseModel, Field

from langchain_pipeline import answer_with_langchain


PROJECT_FOLDER = Path(__file__).resolve().parent
load_dotenv(PROJECT_FOLDER / ".env")

app = FastAPI(title="Synthetic Healthcare FWA RAG")
logger = logging.getLogger("uvicorn.error")


@app.middleware("http")
async def log_ask_request(request: Request, call_next):
    if request.url.path != "/ask":
        return await call_next(request)

    request_id = uuid4().hex
    started_at = perf_counter()
    status_code = 500

    try:
        response = await call_next(request)
        status_code = response.status_code
        response.headers["X-Request-ID"] = request_id
        return response
    finally:
        elapsed_ms = (perf_counter() - started_at) * 1000

        logger.info(
            "rag_request request_id=%s status=%s duration_ms=%.1f",
            request_id,
            status_code,
            elapsed_ms,
        )
security = HTTPBasic(realm="Healthcare FWA RAG")


def require_login(
    credentials: Annotated[HTTPBasicCredentials, Depends(security)],
) -> None:
    username = os.getenv("RAG_APP_USERNAME")
    password = os.getenv("RAG_APP_PASSWORD")

    if not username or not password:
        raise HTTPException(
            status_code=503,
            detail="Application login is unavailable.",
        )

    username_matches = secrets.compare_digest(
        credentials.username.encode("utf-8"),
        username.encode("utf-8"),
    )
    password_matches = secrets.compare_digest(
        credentials.password.encode("utf-8"),
        password.encode("utf-8"),
    )

    if not (username_matches and password_matches):
        raise HTTPException(
            status_code=401,
            detail="Invalid login.",
            headers={"WWW-Authenticate": 'Basic realm="Healthcare FWA RAG"'},
        )


class AskRequest(BaseModel):
    question: str = Field(min_length=1, max_length=2000)


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/", include_in_schema=False, dependencies=[Depends(require_login)])
def home():
    return FileResponse(PROJECT_FOLDER / "index.html")


@app.post("/ask", dependencies=[Depends(require_login)])
def ask(request: AskRequest):
    question = request.question.strip()

    if not question:
        raise HTTPException(
            status_code=422,
            detail="Please provide a question.",
        )

    result = answer_with_langchain(question=question)

    sources = []

    for record in result["cited_sources"]:
        metadata = record["metadata"]

        sources.append({
            "label": record["label"],
            "source": metadata["source"],
            "page": metadata["page"],
            "chunk_number": metadata["chunk_number"],
        })

    return {
        "answer": result["answer"],
        "sources": sources,
        "data_notice": "Synthetic healthcare FWA training data.",
    }
