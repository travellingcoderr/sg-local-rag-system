# Docker: local (Ollama) vs prod (OpenAI / Gemini)

---

## How docker-compose is used (in detail)

### What is Docker Compose?

Docker Compose reads a **`docker-compose.yml`** file and runs multiple **containers** (services) together. It creates a private **network** so containers can reach each other by **service name** (e.g. `ollama`), and it manages **volumes** (persistent data) and **builds** (building images from a Dockerfile). You use one command—`docker compose up`—to start the whole stack.

### What’s in our `docker-compose.yml`?

The file defines **two services** and **one volume**:

1. **`app`** – The Streamlit app (built from the project’s Dockerfile).
2. **`ollama`** – The Ollama server that runs the LLM (pre-built image).
3. **`ollama_data`** – A named volume so downloaded models persist between restarts.

---

### Service 1: `app`

```yaml
app:
  build: .
  ports:
    - "8501:8501"
  environment:
    - LLM_PROVIDER=ollama
    - OLLAMA_HOST=http://ollama:11434
    - OLLAMA_MODEL_NAME=${OLLAMA_MODEL_NAME:-llama3.2:1b}
  env_file:
    - .env
  depends_on:
    - ollama
  volumes:
    - ./logs:/app/logs
```

| Field | What it does |
|-------|----------------|
| **`build: .`** | Build an image using the **Dockerfile** in the current directory (`.`). That Dockerfile installs Python, dependencies, copies the code, and sets the command to `streamlit run Welcome.py`. |
| **`ports: "8501:8501"`** | Maps **host** port 8501 to **container** port 8501. So when you open **http://localhost:8501** on your machine, traffic goes to Streamlit inside the container. |
| **`environment`** | Sets env vars **inside** the container. Here we set which LLM to use (`ollama`) and **where** to find Ollama: **`OLLAMA_HOST=http://ollama:11434`**. The hostname **`ollama`** is the name of the other service; Docker Compose’s network resolves it to that container’s IP. So the app does not use `localhost` for Ollama—it uses the `ollama` container. |
| **`OLLAMA_MODEL_NAME=${OLLAMA_MODEL_NAME:-llama3.2:1b}`** | Uses the env var `OLLAMA_MODEL_NAME` from your **host** (or from `.env`). If it’s not set, it defaults to `llama3.2:1b`. |
| **`env_file: .env`** | Loads variables from a **`.env`** file (if it exists) into the container. So you can put `OLLAMA_MODEL_NAME=mistral` in `.env` and the app will see it. |
| **`depends_on: ollama`** | Tells Compose to **start `ollama` before `app`**. The app container will only start once the `ollama` service is running. It does **not** wait for Ollama to be “ready” (e.g. API up); it only waits for the container to start. |
| **`volumes: ./logs:/app/logs`** | **Bind mount**: the folder **`./logs`** on your host is mounted at **`/app/logs`** in the container. So anything the app writes to `/app/logs` (e.g. `app.log`) appears in your project’s `logs/` folder and persists after the container stops. |

So: the **app** container runs your Streamlit app, exposes it on **localhost:8501**, and is configured to call Ollama at **http://ollama:11434** on the Compose network.

---

### Service 2: `ollama`

```yaml
ollama:
  image: ollama/ollama:latest
  ports:
    - "11434:11434"
  volumes:
    - ollama_data:/root/.ollama
```

| Field | What it does |
|-------|----------------|
| **`image: ollama/ollama:latest`** | No build step. Use the **pre-built** image from Docker Hub named `ollama/ollama`, tag `latest`. This image runs the Ollama server (API + model runtime). |
| **`ports: "11434:11434"`** | Exposes Ollama’s HTTP API on **localhost:11434** on your machine. So you can call **http://localhost:11434** from the host (e.g. to pull models with `ollama pull`), and the **app** container calls **http://ollama:11434** (same port, but using the service name so it goes to this container over the internal network). |
| **`volumes: ollama_data:/root/.ollama`** | Uses a **named volume** `ollama_data`. The path **`/root/.ollama`** inside the container is where Ollama stores pulled models and state. By mounting a volume there, that data is stored in Docker’s volume storage (not in the container filesystem). So when you restart or recreate the `ollama` container, the models you pulled (e.g. `llama3.2:1b`) are still there. |

So: the **ollama** container runs the LLM server, exposes it on **11434**, and keeps models in **`ollama_data`** so they persist.

---

### How the two containers talk

1. **Default network**  
   Docker Compose creates a **default network** for the project (named from the project directory, e.g. `sg-local-rag-system_default`). Both **`app`** and **`ollama`** are attached to this network.

2. **Service name = hostname**  
   On that network, each service is reachable by its **service name**. So from inside the **`app`** container, the hostname **`ollama`** resolves to the IP of the **`ollama`** container. That’s why we set **`OLLAMA_HOST=http://ollama:11434`**: the app’s Python code (e.g. `src/llm.py`) uses this URL to call the Ollama API. The request goes **container → network → ollama container**, not to the host’s localhost.

3. **You** talk to the **app** from the host via **localhost:8501** (port mapping). The **app** talks to **ollama** via **ollama:11434** (internal network).

So the flow is: **You (browser) → localhost:8501 → app container → http://ollama:11434 → ollama container → LLM response back to app → Streamlit → you.**

---

### What happens when you run `docker compose up`

1. **Network**  
   Compose creates the project network if it doesn’t exist.

2. **Volume**  
   The volume **`ollama_data`** is created if it doesn’t exist (used by `ollama`).

3. **`ollama` service**  
   - Image `ollama/ollama:latest` is pulled (if not already present).  
   - Container starts, listens on 11434, mounts `ollama_data` at `/root/.ollama`.  
   - No model is pulled automatically; you run `docker compose exec ollama ollama pull llama3.2:1b` (or your chosen model) the first time.

4. **`app` service** (because of `depends_on`)  
   - The **Dockerfile** is built (if needed): `docker build .` → image with Python, `requirements.txt`, and your code.  
   - Container starts with env `LLM_PROVIDER=ollama`, `OLLAMA_HOST=http://ollama:11434`, etc.  
   - Command runs: `streamlit run Welcome.py --server.port=8501 --server.address=0.0.0.0`.  
   - Streamlit listens on **0.0.0.0:8501** inside the container; the **ports** mapping makes it available as **localhost:8501** on your machine.  
   - `./logs` on your host is mounted at `/app/logs` so logs persist.

5. **You** open **http://localhost:8501** in the browser, use the Chatbot, type a message. The app sends the request to **http://ollama:11434**, the Ollama container runs the model, and the response is streamed back to the app and then to you.

---

### Useful commands

| Command | What it does |
|---------|----------------|
| **`docker compose up --build`** | Build images if needed, create network/volumes, start both services. Logs from both containers appear in one terminal. |
| **`docker compose up -d`** | Same, but run in the **background** (detached). No logs in the terminal. |
| **`docker compose down`** | Stop and remove the containers. Network is removed; **named volume `ollama_data` is kept** (models persist). |
| **`docker compose exec ollama ollama pull llama3.2:1b`** | Run a one-off command **inside** the running `ollama` container: pull the model. Needed once before chat works. |
| **`docker compose exec ollama ollama list`** | List models in the Ollama container. |
| **`docker compose logs -f app`** | Stream logs only from the `app` service. |

---

## Local: run app + Ollama in Docker

Use docker-compose to run the Streamlit app and Ollama on your machine. The app talks to Ollama inside the same compose network.

```bash
# Optional: copy env and tweak
cp .env.example .env

# Build and start
docker compose up --build
```

- App: **http://localhost:8501**
- Ollama API: **http://localhost:11434** (used by the app via `OLLAMA_HOST=http://ollama:11434`)

**First time:** pull a model inside the Ollama container:

```bash
docker compose exec ollama ollama pull llama3.2:1b
```

(Or set `OLLAMA_MODEL_NAME` in `.env` to a model you prefer.)

---

## Prod: use OpenAI or Gemini instead of Ollama

Do **not** run the Ollama service. Run only the app (e.g. same Dockerfile, or on a host/VM) and set environment variables so the app uses OpenAI or Gemini.

### OpenAI

```bash
export LLM_PROVIDER=openai
export OPENAI_API_KEY=sk-...
export OPENAI_MODEL=gpt-4o-mini   # or gpt-4o, etc.
# Run the app (e.g. docker run or your orchestrator)
```

### Gemini

```bash
export LLM_PROVIDER=gemini
export GEMINI_API_KEY=...
export GEMINI_MODEL=gemini-1.5-flash   # or gemini-1.5-pro, etc.
# Run the app
```

### Example: run app image in prod with OpenAI

```bash
docker build -t sg-rag-app .
docker run -p 8501:8501 \
  -e LLM_PROVIDER=openai \
  -e OPENAI_API_KEY=sk-... \
  -e OPENAI_MODEL=gpt-4o-mini \
  sg-rag-app
```

---

## Summary

| Environment | LLM_PROVIDER | What to run | Notes |
|-------------|--------------|-------------|--------|
| Local       | `ollama`     | `docker compose up` (app + ollama) | Set `OLLAMA_HOST=http://ollama:11434` |
| Prod        | `openai`     | App only    | Set `OPENAI_API_KEY`, `OPENAI_MODEL` |
| Prod        | `gemini`     | App only    | Set `GEMINI_API_KEY`, `GEMINI_MODEL` |

All other config (embedding model, OpenSearch, etc.) can still be overridden via env; see `.env.example`.

---

## Freeing Docker space (out of space on Mac)

The app image is large (~3–5GB+) because it includes PyTorch and sentence-transformers. Ollama + a model add more. If you run out of space, reclaim it from Docker first.

### 1. See what Docker is using

```bash
docker system df
```

Shows: images, containers, local volumes, build cache.

### 2. Remove unused stuff (safe, no data you need)

```bash
# Remove stopped containers, unused networks, dangling images
docker system prune -f

# Also remove build cache (frees a lot after a failed build)
docker builder prune -f

# Remove all unused images (not just dangling)
docker image prune -a -f
```

**Warning:** `docker image prune -a` removes every image not used by a container. After this, the next `docker compose up --build` will re-download the Ollama image and rebuild the app image.

### 3. Remove unused volumes (careful)

```bash
docker volume ls
docker volume prune -f
```

**Warning:** `volume prune` removes volumes not used by any container. Our **`ollama_data`** is used by the `ollama` service when it’s running. If you run `docker compose down` and then `docker volume prune`, `ollama_data` can be deleted and you’ll lose pulled models (you’d pull them again). To remove **only** volumes you’re sure you don’t need, use `docker volume rm <name>` for specific ones instead of `prune`.

### 4. Nuclear option: reset Docker disk usage (Docker Desktop)

- **Docker Desktop** → **Settings** (gear) → **Resources** → **Advanced** → **Disk image size**, or  
- **Troubleshoot** → **Clean / Purge data** (removes all containers, images, volumes; you start fresh).

### 5. After freeing space, try again

```bash
docker compose up --build
```

If the **build** fails again (out of space during `pip install`), ensure at least **10–15 GB free** before building; the Python + PyTorch layer is large. You can also run the app **without Docker** (venv on your Mac) to avoid image size; see README for `streamlit run Welcome.py`.
