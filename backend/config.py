"""
config.py
---------
Central configuration for the University Student Support Assistant backend.

All values can be overridden using environment variables, which makes it
easy to change settings between development and "production" without
touching the code (e.g. when you containerise the app with Docker, or
move the LLM to a different host).
"""

import os


class Settings:
    # --- Ollama / Local LLM settings -------------------------------------
    # Base URL where Ollama is being served. Default is the standard local
    # Ollama address used when you run `ollama serve`.
    OLLAMA_BASE_URL: str = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")

    # The model name must already be pulled locally, e.g:
    #   ollama pull llama3.2:1b
    OLLAMA_MODEL: str = os.getenv("OLLAMA_MODEL", "llama3.2:1b")

    # How long (seconds) the backend will wait for the model to respond
    # before returning a "model not responding" error to the frontend.
    OLLAMA_TIMEOUT: int = int(os.getenv("OLLAMA_TIMEOUT", "60"))

    # --- API settings -------------------------------------------------------
    API_TITLE: str = "University Student Support Assistant API"
    API_VERSION: str = "1.0.0"

    # Allow the frontend (served from a different port/file) to call the API.
    CORS_ORIGINS: list = ["*"]  # In production, replace "*" with real origins.

    # --- Logging --------------------------------------------------------
    LOG_DIR: str = os.getenv("LOG_DIR", os.path.join(os.path.dirname(__file__), "logs"))
    LOG_FILE: str = os.path.join(LOG_DIR, "app.log")

    # --- System Prompt ----------------------------------------------------
    # This is the "improved" prompt referenced in Task 6 of the assignment.
    # It grounds the assistant in its role and limits it to university topics.
    SYSTEM_PROMPT: str = (
        "You are the University Student Support Assistant, a helpful and concise "
        "AI assistant for university students. You answer questions ONLY about "
        "university-related matters such as course registration, examination "
        "rules, library services, ICT support, hostel applications, fee payment, "
        "the academic calendar, and student conduct. "
        "If a student asks something unrelated to university services, politely "
        "explain that you can only help with university-related questions. "
        "Keep answers short, clear, and use simple, friendly language. "
        "If FAQ context is provided below, prioritise that information in your answer."
    )


settings = Settings()
