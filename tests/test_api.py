"""
test_api.py
-----------
Simple test script for the University Student Support Assistant API
(Task 5: The Created API Test Script).

These tests cover:
  - /health endpoint returns 200 and expected fields
  - /ask endpoint returns a successful answer for a valid question
  - /ask endpoint rejects an empty question (validation error)
  - /ask endpoint response includes an FAQ topic when one matches

Run with:
    pytest tests/test_api.py -v

Note: these tests call the REAL backend app in-process using FastAPI's
TestClient, but the /ask test still needs Ollama running locally
(since llm_client.py makes a real HTTP call to Ollama). If Ollama is
not running, the LLM-dependent tests will be skipped automatically.
"""

import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import pytest
import requests
from fastapi.testclient import TestClient

from backend.main import app
from backend.config import settings

client = TestClient(app)


def ollama_is_running() -> bool:
    try:
        requests.get(settings.OLLAMA_BASE_URL, timeout=2)
        return True
    except requests.exceptions.RequestException:
        return False


def test_health_endpoint():
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "model" in data


def test_ask_rejects_empty_question():
    response = client.post("/ask", json={"question": "   "})
    # Pydantic validation error -> FastAPI returns 422 Unprocessable Entity
    assert response.status_code == 422


def test_ask_rejects_missing_question_field():
    response = client.post("/ask", json={})
    assert response.status_code == 422


@pytest.mark.skipif(not ollama_is_running(), reason="Ollama is not running locally")
def test_ask_returns_answer_for_valid_question():
    response = client.post("/ask", json={"question": "How do I register for courses?"})
    assert response.status_code == 200
    data = response.json()
    assert "answer" in data
    assert len(data["answer"]) > 0
    assert data["response_time_seconds"] >= 0


@pytest.mark.skipif(not ollama_is_running(), reason="Ollama is not running locally")
def test_ask_matches_faq_topic():
    response = client.post("/ask", json={"question": "How do I borrow a book from the library?"})
    assert response.status_code == 200
    data = response.json()
    assert data["faq_topic"] == "Library Services"


if __name__ == "__main__":
    sys.exit(pytest.main([__file__, "-v"]))
