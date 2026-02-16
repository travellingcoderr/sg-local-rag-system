# Build and run the Streamlit app. Use with docker-compose for local (Ollama) or set env for prod (OpenAI/Gemini).
FROM python:3.11-slim

WORKDIR /app

# Install deps (optional: split requirements for smaller prod image)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
# Exclude dev/optional at build if needed via .dockerignore

# Streamlit needs to bind to 0.0.0.0 inside the container
ENV STREAMLIT_SERVER_ADDRESS=0.0.0.0
ENV STREAMLIT_SERVER_HEADLESS=true

EXPOSE 8501

CMD ["streamlit", "run", "Welcome.py", "--server.port=8501", "--server.address=0.0.0.0"]
