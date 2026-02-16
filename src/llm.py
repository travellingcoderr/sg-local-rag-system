"""
LLM abstraction: Ollama (local), OpenAI, or Gemini.
Switch via env LLM_PROVIDER=ollama|openai|gemini. All backends expose the same streaming interface.
"""
import logging
from typing import Any, Dict, Iterator, List, Optional

from src.constants import (
    GEMINI_API_KEY,
    GEMINI_MODEL,
    LLM_PROVIDER,
    OLLAMA_HOST,
    OLLAMA_MODEL_NAME,
    OPENAI_API_KEY,
    OPENAI_MODEL,
)
from src.utils import setup_logging

setup_logging()
logger = logging.getLogger(__name__)


def _build_messages(chat_history: List[Dict[str, str]], new_prompt: str) -> List[Dict[str, str]]:
    """Build messages list for API: last N turns + new user message."""
    messages: List[Dict[str, str]] = []
    max_turns = 10
    for msg in chat_history[-max_turns * 2 :]:
        messages.append({"role": msg["role"], "content": msg["content"]})
    messages.append({"role": "user", "content": new_prompt})
    return messages


def _stream_ollama(prompt: str, chat_history: List[Dict[str, str]], temperature: float) -> Optional[Iterator[Any]]:
    """Stream from Ollama. Yields chunks with ['message']['content']."""
    import ollama

    messages = _build_messages(chat_history, prompt)
    try:
        # Point client at OLLAMA_HOST (e.g. http://ollama:11434 in Docker)
        client = ollama.Client(host=OLLAMA_HOST)
        stream = client.chat(
            model=OLLAMA_MODEL_NAME,
            messages=messages,
            stream=True,
            options={"temperature": temperature},
        )
        return stream
    except Exception as e:
        logger.error(f"Ollama stream error: {e}")
        return None


def _stream_openai(prompt: str, chat_history: List[Dict[str, str]], temperature: float) -> Optional[Iterator[Any]]:
    """Stream from OpenAI. Yields chunks compatible with same shape as Ollama for the UI."""
    if not OPENAI_API_KEY:
        logger.error("OPENAI_API_KEY not set")
        return None
    try:
        from openai import OpenAI

        client = OpenAI(api_key=OPENAI_API_KEY)
        messages = _build_messages(chat_history, prompt)
        # OpenAI wants {"role": "user", "content": "..."} and optionally system
        api_messages = [{"role": m["role"], "content": m["content"]} for m in messages]
        stream = client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=api_messages,
            stream=True,
            temperature=temperature,
        )
        # Normalize to same shape as Ollama: yield {"message": {"content": delta}}
        for chunk in stream:
            delta = chunk.choices[0].delta if chunk.choices else None
            if delta and getattr(delta, "content", None):
                yield {"message": {"content": delta.content}}
    except Exception as e:
        logger.error(f"OpenAI stream error: {e}")
        return None


def _stream_gemini(prompt: str, chat_history: List[Dict[str, str]], temperature: float) -> Optional[Iterator[Any]]:
    """Stream from Google Gemini. Yields chunks with ['message']['content'] for UI."""
    if not GEMINI_API_KEY:
        logger.error("GEMINI_API_KEY not set")
        return None
    try:
        import google.generativeai as genai

        genai.configure(api_key=GEMINI_API_KEY)
        model = genai.GenerativeModel(GEMINI_MODEL)
        # Build a single prompt with conversation history for context
        messages = _build_messages(chat_history, prompt)
        prompt_with_history = "\n".join(
            f"{m['role'].capitalize()}: {m['content']}" for m in messages
        )
        response = model.generate_content(prompt_with_history, stream=True)
        for chunk in response:
            if chunk.text:
                yield {"message": {"content": chunk.text}}
    except Exception as e:
        logger.error(f"Gemini stream error: {e}")
        return None


def generate_response_streaming(
    prompt: str,
    chat_history: Optional[List[Dict[str, str]]] = None,
    temperature: float = 0.7,
    context: Optional[str] = None,
) -> Optional[Iterator[Any]]:
    """
    Stream LLM response. Backend is chosen by LLM_PROVIDER (ollama | openai | gemini).
    All backends yield chunks with chunk["message"]["content"] for the UI.
    If context is provided (from RAG), it is prepended to the user prompt so the LLM answers using your documents.
    """
    chat_history = chat_history or []
    if context and context.strip():
        prompt = (
            "Use the following context from the uploaded documents to answer the question. "
            "If the context does not contain relevant information, say so.\n\n"
            f"Context:\n{context.strip()}\n\n"
            f"Question: {prompt}"
        )
    if LLM_PROVIDER == "openai":
        return _stream_openai(prompt, chat_history, temperature)
    if LLM_PROVIDER == "gemini":
        return _stream_gemini(prompt, chat_history, temperature)
    return _stream_ollama(prompt, chat_history, temperature)


def ensure_model_pulled(model_name: str) -> bool:
    """Ollama: ensure model is available. OpenAI/Gemini: ensure API key is set."""
    if LLM_PROVIDER == "openai":
        return bool(OPENAI_API_KEY)
    if LLM_PROVIDER == "gemini":
        return bool(GEMINI_API_KEY)
    
    # For Ollama: check if server is reachable with timeout, then check/pull model
    try:
        import ollama
        import requests
        
        # Quick health check: try to reach Ollama with a short timeout (3 seconds)
        try:
            health_url = OLLAMA_HOST.rstrip("/") + "/api/tags"
            response = requests.get(health_url, timeout=3)
            if response.status_code != 200:
                logger.warning(f"Ollama server at {OLLAMA_HOST} returned status {response.status_code}. Is Ollama running?")
                return False
        except requests.exceptions.RequestException as e:
            logger.warning(f"Ollama server at {OLLAMA_HOST} is not reachable: {e}. Is Ollama running?")
            return False
        
        # If reachable, check/pull model
        client = ollama.Client(host=OLLAMA_HOST)
        resp = client.list()
        if isinstance(resp, dict):
            models = resp.get("models", [])
            names = [m.get("name", m.get("model", "")) for m in models]
        else:
            models = getattr(resp, "models", [])
            names = [getattr(m, "model", getattr(m, "name", "")) for m in models]
        if model_name not in names:
            logger.info(f"Pulling model {model_name}...")
            client.pull(model_name)
        return True
    except Exception as e:
        logger.warning(f"Could not check/pull Ollama model ({e}). Is Ollama running at {OLLAMA_HOST}?")
        return False
