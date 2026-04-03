@echo off
echo =^> Setting up RAG Summarizer...

REM 1. Copy .env if not exists
IF NOT EXIST .env (
    copy .env.example .env
    echo =^> Created .env from .env.example
) ELSE (
    echo =^> .env already exists, skipping
)

REM 2. Create required directories
IF NOT EXIST fs\plaintables mkdir fs\plaintables
IF NOT EXIST fs\vector_stores mkdir fs\vector_stores
IF NOT EXIST uploads mkdir uploads
echo =^> Directories created

REM 3. Install Python dependencies
echo =^> Installing Python dependencies...
pip install -r requirements.txt

REM 4. Check if Ollama is installed
where ollama >nul 2>&1
IF ERRORLEVEL 1 (
    echo =^> Ollama not found.
    echo     Please download and install Ollama from: https://ollama.com/download
    echo     Then re-run this script.
    pause
    exit /b 1
) ELSE (
    echo =^> Ollama found
)

REM 5. Pull the model
echo =^> Pulling Ollama model (qwen2.5:1.5b)...
ollama pull qwen2.5:1.5b

REM 6. Start Ollama server in background
echo =^> Starting Ollama server in background...
start /B ollama serve
timeout /t 3 >nul

REM 7. Start the app
echo =^> Starting RAG Summarizer on http://localhost:8000 ...
echo     (Use --host 0.0.0.0 instead of 127.0.0.1 to allow network access)
uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
