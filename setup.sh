#!/bin/bash
set -e

echo "==> Setting up RAG Summarizer..."

# 1. Copy .env if not exists
if [ ! -f .env ]; then
    cp .env.example .env
    echo "==> Created .env from .env.example"
else
    echo "==> .env already exists, skipping"
fi

# 2. Create required directories
mkdir -p fs/plaintables fs/vector_stores uploads
echo "==> Directories created"

# 3. Install Python dependencies
echo "==> Installing Python dependencies..."
pip install -r requirements.txt

# 4. Install Ollama if not installed
if ! command -v ollama &> /dev/null; then
    echo "==> Installing Ollama..."
    curl -fsSL https://ollama.com/install.sh | sh
else
    echo "==> Ollama already installed"
fi

# 5. Pull the model
echo "==> Pulling Ollama model (qwen2.5:1.5b)..."
ollama pull qwen2.5:1.5b

# 6. Start Ollama in background if not already running
if ! curl -s http://localhost:11434/api/tags > /dev/null 2>&1; then
    echo "==> Starting Ollama server in background..."
    ollama serve &
    sleep 3
else
    echo "==> Ollama already running"
fi

# 7. Start the app
echo "==> Starting RAG Summarizer on http://localhost:8000 ..."
echo "    (Use --host 0.0.0.0 instead of 127.0.0.1 to allow network access)"
uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
