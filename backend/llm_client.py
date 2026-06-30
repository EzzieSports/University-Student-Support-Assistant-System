"""
llm_client.py
--------------
Handles all communication between the FastAPI backend and the locally
hosted LLM served by Ollama.

This module is intentionally kept separate from main.py so that the
"backend logic" (routes, validation) stays decoupled from the
"LLM communication logic" (HTTP calls to Ollama). This separation
makes it easy to swap Ollama for another local LLM server later
without touching the API routes.
"""

import logging
import requests

from backend.config import settings

logger = logging.getLogger("student_support_assistant")


class LLMConnectionError(Exception):
    """Raised when the backend cannot reach the Ollama server at all
    (e.g. Ollama is not running)."""


class LLMResponseError(Exception):
    """Raised when Ollama is reachable but returns an error or an
    unexpected/empty response."""


def build_prompt(question: str, faq_context: str | None = None) -> str:
    """
    Combine the system prompt, optional FAQ context (bonus RAG-lite
    feature) and the student's question into a single prompt string
    sent to the model.
    """
    parts = [settings.SYSTEM_PROMPT]

    if faq_context:
        parts.append(f"\nRelevant FAQ information:\n{faq_context}")

    parts.append(f"\nStudent question: {question}\nAnswer:")
    return "\n".join(parts)


def ask_llm(question: str, faq_context: str | None = None) -> str:
    """
    Send a question (plus optional FAQ context) to the local Ollama
    model and return the generated answer as plain text.

    Raises:
        LLMConnectionError: if Ollama is not running / unreachable.
        LLMResponseError: if Ollama responds with an error or bad payload.
    """
    prompt = build_prompt(question, faq_context)
    url = f"{settings.OLLAMA_BASE_URL}/api/generate"

    payload = {
        "model": settings.OLLAMA_MODEL,
        "prompt": prompt,
        "stream": False,
    }

    try:
        response = requests.post(url, json=payload, timeout=settings.OLLAMA_TIMEOUT)
    except requests.exceptions.ConnectionError as exc:
        logger.error("Could not connect to Ollama at %s: %s", settings.OLLAMA_BASE_URL, exc)
        raise LLMConnectionError(
            f"Could not connect to the local LLM server at {settings.OLLAMA_BASE_URL}. "
            "Is Ollama running? Try: ollama serve"
        ) from exc
    except requests.exceptions.Timeout as exc:
        logger.error("Ollama request timed out after %s seconds", settings.OLLAMA_TIMEOUT)
        raise LLMResponseError(
            f"The model did not respond within {settings.OLLAMA_TIMEOUT} seconds."
        ) from exc

    if response.status_code != 200:
        logger.error("Ollama returned status %s: %s", response.status_code, response.text)
        raise LLMResponseError(
            f"The local model returned an error (status {response.status_code}). "
            f"Make sure the model '{settings.OLLAMA_MODEL}' has been pulled."
        )

    try:
        data = response.json()
        answer = data.get("response", "").strip()
    except ValueError as exc:
        logger.error("Failed to parse Ollama response as JSON: %s", exc)
        raise LLMResponseError("Received an unreadable response from the local model.") from exc

    if not answer:
        raise LLMResponseError("The model returned an empty response.")

    return answer
