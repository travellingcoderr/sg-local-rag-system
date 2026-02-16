"""
Chat: prompt → LLM → response. Backend is selected by LLM_PROVIDER (ollama | openai | gemini).
See src/llm.py for the actual provider implementations.
"""
from src.llm import ensure_model_pulled, generate_response_streaming

__all__ = ["ensure_model_pulled", "generate_response_streaming"]
