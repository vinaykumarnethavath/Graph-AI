# Deployment Guide: Graph AI (Unified)

This guide explains how to deploy the Graph AI application as a single unit using Docker or a local production build.

## Prerequisites
-   Python 3.10+
-   Node.js 18+
-   Docker (Recommended)
-   Groq API Key (in `.env`)

---

## 1. One-Click Deployment (Docker) - RECOMMENDED

The easiest way to deploy is using the provided multi-stage `Dockerfile`. This will build the frontend and serve it directly via the FastAPI backend.

1.  **Build the Image**:
    ```bash
    docker build -t graph-ai .
    ```
2.  **Run the Container**:
    ```bash
    docker run -p 8000:8000 --env-file .env graph-ai
    ```
    The app will be available at `http://localhost:8000`.

### Using Docker Compose
Simply run:
```bash
docker-compose up --build
```

---

## 2. Local Production Build (Manual)

If you don't want to use Docker, follow these steps to serve the frontend via FastAPI:

1.  **Build Frontend**:
    ```bash
    cd frontend
    npm install
    npm run build
    ```
2.  **Prepare Static Files**:
    Copy everything from `frontend/dist/` to `backend/static/`.
3.  **Run Backend**:
    ```bash
    cd ..
    $env:PYTHONPATH="."; python backend/run_server.py
    ```
    Access the app at `http://localhost:8000`.

---

## 3. Cloud Deployment (Render / Railway / AWS)
-   **Railway/Render**: Point to the root directory. They will automatically detect the `Dockerfile` and deploy the entire project in one container.
-   **Environment Variables**: Ensure `GROQ_API_KEY` is added to the cloud provider's dashboard.

## Troubleshooting
-   **Vite Proxy**: In production (unified build), the frontend communicates with the backend on the same origin, so ensure `client.js` uses `BASE_URL = ""`.
-   **Graph Path**: The `.env` should use `GRAPH_PATH=dataset/processed_data/graph.gpickle`.
