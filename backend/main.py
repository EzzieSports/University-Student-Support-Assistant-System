"""
main.py
-------
FastAPI backend for the University Student Support Assistant.

Endpoints:
    GET  /health  -> simple health check used by the frontend and tests
    POST /ask     -> receives a student question, optionally enriches it
                      with FAQ context, sends it to the local LLM via
                      llm_client.py, logs the interaction, and returns
                      the generated answer.

Run with:
    uvicorn backend.main:app --reload
"""

import logging
import os
import time
from datetime import datetime

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, field_validator

from backend.config import settings
from backend.faq import find_relevant_faq
from backend.llm_client import ask_llm, LLMConnectionError, LLMResponseError

# --------------------------------------------------------------------------
# Logging setup (Task 8: Logging)
# --------------------------------------------------------------------------
os.makedirs(settings.LOG_DIR, exist_ok=True)

logger = logging.getLogger("student_support_assistant")
logger.setLevel(logging.INFO)

if not logger.handlers:
    file_handler = logging.FileHandler(settings.LOG_FILE, encoding="utf-8")
    formatter = logging.Formatter(
        fmt="%(asctime)s | %(levelname)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    # Also print logs to the console so they're visible while the
    # server is running (useful for the "FastAPI running" screenshot).
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)


# --------------------------------------------------------------------------
# FastAPI app setup
# --------------------------------------------------------------------------
app = FastAPI(title=settings.API_TITLE, version=settings.API_VERSION)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# --------------------------------------------------------------------------
# Request / Response models
# --------------------------------------------------------------------------
class AskRequest(BaseModel):
    question: str

    @field_validator("question")
    @classmethod
    def question_must_not_be_empty(cls, value: str) -> str:
        if not value or not value.strip():
            raise ValueError("Question must not be empty.")
        return value.strip()


class AskResponse(BaseModel):
    answer: str
    faq_topic: str | None = None
    response_time_seconds: float


# --------------------------------------------------------------------------
# Routes
# --------------------------------------------------------------------------
@app.get("/health")
def health_check():
    """Simple endpoint the frontend uses to check the backend is alive."""
    return {"status": "ok", "service": settings.API_TITLE, "model": settings.OLLAMA_MODEL}


@app.post("/ask", response_model=AskResponse)
def ask_question(payload: AskRequest):
    """
    Receive a student's question, look up FAQ context (bonus feature),
    forward everything to the local LLM, log the interaction, and
    return the answer.
    """
    question = payload.question
    timestamp = datetime.now().isoformat()

    # Bonus feature: simple FAQ keyword retrieval, used as lightweight RAG context.
    faq_topic, faq_answer = find_relevant_faq(question)

    logger.info("Received question: %s", question)

    start_time = time.time()
    try:
        answer = ask_llm(question, faq_context=faq_answer)
    except LLMConnectionError as exc:
        logger.error("[%s] Connection error: %s", timestamp, exc)
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except LLMResponseError as exc:
        logger.error("[%s] Model error: %s", timestamp, exc)
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    except Exception as exc:  # noqa: BLE001 - final safety net, never crash the API
        logger.error("[%s] Unexpected error: %s", timestamp, exc)
        raise HTTPException(status_code=500, detail="An unexpected error occurred.") from exc

    elapsed = round(time.time() - start_time, 2)

    logger.info(
        "Generated answer (%.2fs) | FAQ topic: %s | Answer: %s",
        elapsed,
        faq_topic or "none",
        answer,
    )

    return AskResponse(answer=answer, faq_topic=faq_topic, response_time_seconds=elapsed)


@app.get("/")
def root():
    return {
        "message": "University Student Support Assistant API is running.",
        "docs": "/docs",
        "health": "/health",
    }
