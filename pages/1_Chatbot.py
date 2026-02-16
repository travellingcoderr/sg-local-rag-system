"""
Interactive Chatbot: prompt → LLM (Ollama) → response.
Uses src.chat to send your text to the local model and stream the reply back.
"""
import logging
import os

import streamlit as st

from src.chat import ensure_model_pulled, generate_response_streaming
from src.constants import LLM_PROVIDER, OLLAMA_MODEL_NAME, OPENAI_MODEL, GEMINI_MODEL
from src.utils import setup_logging

def _model_display_name() -> str:
    if LLM_PROVIDER == "openai":
        return OPENAI_MODEL
    if LLM_PROVIDER == "gemini":
        return GEMINI_MODEL
    return OLLAMA_MODEL_NAME

setup_logging()
logger = logging.getLogger(__name__)

st.set_page_config(page_title="Chatbot", page_icon="🤖", layout="centered")

st.markdown(
    """
    <style>
    body { background-color: #f0f8ff; color: #002B5B; }
    .block-container { background-color: white; border-radius: 10px; padding: 20px; box-shadow: 0px 4px 12px rgba(0, 0, 0, 0.1); }
    h1, h2, h3 { color: #006d77; }
    .stChatMessage { background-color: #e0f7fa; color: #006d77; padding: 10px; border-radius: 5px; margin-bottom: 10px; }
    </style>
    """,
    unsafe_allow_html=True,
)

if os.path.exists("images/purpleai.png"):
    st.sidebar.image("images/purpleai.png", width=180)

# Sidebar: temperature (and later: RAG toggle, num results)
if "temperature" not in st.session_state:
    st.session_state["temperature"] = 0.7
st.session_state["temperature"] = st.sidebar.slider(
    "Response temperature",
    min_value=0.0,
    max_value=1.0,
    value=st.session_state["temperature"],
    step=0.1,
)

st.title("🤖 Chatbot")
st.caption(f"LLM: {LLM_PROVIDER} ({_model_display_name()}). Your message is streamed back below.")

# Ensure model is ready (for Ollama: pull if needed; OpenAI/Gemini: just need API key)
if "ollama_ready" not in st.session_state:
    with st.spinner("Checking LLM connection..."):
        st.session_state["ollama_ready"] = ensure_model_pulled(OLLAMA_MODEL_NAME)
if not st.session_state["ollama_ready"]:
    if LLM_PROVIDER == "ollama":
        st.error(
            f"**Ollama is not running or not reachable.**\n\n"
            f"To use the chatbot:\n"
            f"1. Install Ollama from [ollama.ai](https://ollama.ai)\n"
            f"2. Start Ollama (it usually runs automatically after installation)\n"
            f"3. Pull a model: `ollama pull {OLLAMA_MODEL_NAME}`\n"
            f"4. Refresh this page\n\n"
            f"Configured endpoint: `{OLLAMA_MODEL_NAME}` at `{OLLAMA_HOST}`"
        )
    else:
        st.warning(f"Could not reach LLM. For {LLM_PROVIDER}: check your API key configuration.")

# Chat history: list of {"role": "user"|"assistant", "content": "..."}
if "chat_history" not in st.session_state:
    st.session_state["chat_history"] = []

# Show previous messages
for msg in st.session_state["chat_history"]:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# New user input
if prompt := st.chat_input("Type your message here..."):
    # Append user message and show it
    st.session_state["chat_history"].append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Stream assistant reply
    with st.chat_message("assistant"):
        response_placeholder = st.empty()
        response_text = ""

        stream = generate_response_streaming(
            prompt,
            chat_history=st.session_state["chat_history"][:-1],  # exclude current prompt
            temperature=st.session_state["temperature"],
        )

        if stream is not None:
            for chunk in stream:
                # Ollama stream: chunk can be dict with ["message"]["content"] or object with .message.content
                part = ""
                if isinstance(chunk, dict):
                    msg = chunk.get("message") or chunk
                    part = msg.get("content", "") if isinstance(msg, dict) else ""
                elif hasattr(chunk, "message"):
                    part = getattr(chunk.message, "content", "") or ""
                if part:
                    response_text += part
                    response_placeholder.markdown(response_text + "▌")
            response_placeholder.markdown(response_text)
            st.session_state["chat_history"].append({"role": "assistant", "content": response_text})
        else:
            st.error("Failed to get a response from the LLM. Check that Ollama is running and the model is available.")
