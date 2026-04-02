# Prerequisites — Bootstrap of RAG Workshop

This guide walks you through everything you need to install **before** the workshop starts, on your specific operating system.

> Estimated setup time: **15–25 minutes**

---

## What You Need

| Tool | Version | Purpose |
|---|---|---|
| Python | 3.10 – 3.13 | Runs the FastAPI application |
| pip | latest | Installs Python packages |
| Git | any recent | Clone the repository |
| Ollama | latest | Runs the local LLM |
| LLM model | qwen2.5:1.5b | The language model (pulled via Ollama) |
| (optional) virtualenv / venv | — | Isolates Python dependencies |

---

## macOS

### 1. Install Homebrew (if not already installed)

Homebrew is the standard package manager for macOS.

```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
```

Verify:

```bash
brew --version
```

---

### 2. Install Python 3.11

```bash
brew install python@3.11
```

Verify:

```bash
python3 --version
# Python 3.11.x
```

> If your system python3 still points to an older version, use the explicit path:
> `/opt/homebrew/bin/python3.11`

---

### 3. Install Git

Git is usually pre-installed on macOS. Check first:

```bash
git --version
```

If not installed:

```bash
brew install git
```

---

### 4. Install Ollama

Download from the official site and run the installer:

```
https://ollama.com/download/mac
```

After installation, start the Ollama server:

```bash
ollama serve
```

Leave this terminal window open. Open a **new** terminal for the next steps.

---

### 5. Pull the LLM model

```bash
ollama pull qwen2.5:1.5b
```

This downloads ~1 GB. Verify it worked:

```bash
ollama list
# NAME                    ID            SIZE    MODIFIED
# qwen2.5:1.5b            ...           ...     ...
```

---

### 6. Clone the repository

```bash
git clone https://github.com/HariGHI/rag-summarizer.git
cd rag-summarizer
```

---

### 7. Create a virtual environment and install dependencies

```bash
python3 -m venv .venv
source .venv/bin/activate

pip install --upgrade pip
pip install -r requirements.txt
```

---

### 8. Verify everything works

```bash
# Make sure ollama serve is running in another terminal, then:
python -m uvicorn app.main:app --reload
```

Open your browser at `http://localhost:8000` — you should see the RAG Summarizer UI.

---

---

## Windows

> Use **PowerShell** (run as Administrator) for all commands unless noted.

---

### 1. Install Python 3.11

Download the installer from:

```
https://www.python.org/downloads/windows/
```

During installation:
- Check **"Add Python to PATH"** before clicking Install
- Check **"Install pip"**

Verify in a new PowerShell window:

```powershell
python --version
# Python 3.11.x

pip --version
```

---

### 2. Install Git

Download Git for Windows:

```
https://git-scm.com/download/win
```

Use default settings during installation. Verify:

```powershell
git --version
```

---

### 3. Install Ollama

Download the Windows installer from:

```
https://ollama.com/download/windows
```

Run the installer. Ollama starts automatically as a background service after installation.

Verify in PowerShell:

```powershell
ollama --version
```

---

### 4. Pull the LLM model

```powershell
ollama pull qwen2.5:1.5b
```

Verify:

```powershell
ollama list
```

---

### 5. Clone the repository

```powershell
git clone https://github.com/HariGHI/rag-summarizer.git
cd rag-summarizer
```

---

### 6. Create a virtual environment and install dependencies

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1

pip install --upgrade pip
pip install -r requirements.txt
```

> If you get an error about script execution being disabled, run this first:
> ```powershell
> Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
> ```

---

### 7. Verify everything works

```powershell
python -m uvicorn app.main:app --reload
```

Open your browser at `http://localhost:8000`.

---

---

## Ubuntu / Linux

> Tested on Ubuntu 22.04 LTS and 24.04 LTS.

---

### 1. Update system packages

```bash
sudo apt update && sudo apt upgrade -y
```

---

### 2. Install Python 3.11

Ubuntu 22.04 ships with Python 3.10. Add the deadsnakes PPA to get 3.11:

```bash
sudo apt install -y software-properties-common
sudo add-apt-repository ppa:deadsnakes/ppa -y
sudo apt update
sudo apt install -y python3.11 python3.11-venv python3.11-distutils
```

Verify:

```bash
python3.11 --version
# Python 3.11.x
```

Install pip for 3.11:

```bash
curl -sS https://bootstrap.pypa.io/get-pip.py | python3.11
```

> Ubuntu 24.04 already ships with Python 3.12 — use `python3` directly and skip the PPA.

---

### 3. Install Git

```bash
sudo apt install -y git
git --version
```

---

### 4. Install Ollama

Run the official install script:

```bash
curl -fsSL https://ollama.com/install.sh | sh
```

Start the Ollama server:

```bash
ollama serve &
```

> The `&` runs it in the background. To keep it running across sessions, use a separate terminal or set it up as a systemd service (see below).

Verify:

```bash
ollama --version
```

**Optional — run Ollama as a systemd service** (so it starts automatically on boot):

```bash
sudo systemctl enable ollama
sudo systemctl start ollama
```

---

### 5. Pull the LLM model

```bash
ollama pull qwen2.5:1.5b
```

Verify:

```bash
ollama list
```

---

### 6. Clone the repository

```bash
git clone https://github.com/HariGHI/rag-summarizer.git
cd rag-summarizer
```

---

### 7. Create a virtual environment and install dependencies

```bash
python3.11 -m venv .venv
source .venv/bin/activate

pip install --upgrade pip
pip install -r requirements.txt
```

---

### 8. Verify everything works

```bash
python -m uvicorn app.main:app --reload
```

Open your browser at `http://localhost:8000`.

---

---

## Common Issues

### "ollama: command not found"

- **macOS / Linux** — Ollama was not added to PATH. Try opening a new terminal or run:
  ```bash
  export PATH=$PATH:$HOME/.ollama/bin
  ```
- **Windows** — Restart PowerShell after installation.

---

### Python package install fails with "error: Microsoft Visual C++ required" (Windows)

Install the Microsoft C++ Build Tools:

```
https://visualstudio.microsoft.com/visual-cpp-build-tools/
```

Select **"Desktop development with C++"** and retry `pip install`.

---

### "sentence-transformers" takes a long time to install

This is normal — it pulls PyTorch and several ML dependencies (~500 MB). Let it run.

---

### Port 8000 already in use

Run the app on a different port:

```bash
python -m uvicorn app.main:app --reload --port 8001
```

---

### Ollama model download is slow

The `qwen2.5:1.5b` model is ~1 GB. Download it **before the workshop** on a good internet connection. If you are on a slow connection, `tinyllama` (~600 MB) can be used as a fallback:

```bash
ollama pull tinyllama
```

Then set the model in `.env`:

```
OLLAMA_MODEL=tinyllama
```

---

## Quick Checklist

Before the workshop, verify each item:

- [ ] `python3 --version` → 3.10 or higher
- [ ] `git --version` → any version
- [ ] `ollama --version` → any version
- [ ] `ollama list` → shows `qwen2.5:1.5b`
- [ ] `pip install -r requirements.txt` → completes without errors
- [ ] `python -m uvicorn app.main:app --reload` → server starts on port 8000
- [ ] Browser at `http://localhost:8000` → shows the RAG Summarizer UI
