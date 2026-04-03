# 🚀 RAG Summarizer

A production-grade **Retrieval-Augmented Generation (RAG)** API for document summarization and Q&A, built with FastAPI and LanceDB.

Built for the **"Bootstrap of RAG"** workshop by **Kuruba Harish** (April 3rd, 2026).

---

## ✨ Features

- 📁 **Spaces** — Organize documents into workspaces
- 📄 **Artifacts** — Upload and auto-chunk markdown files
- 🔍 **Retrieval** — Vector, FTS, and hybrid search
- 🤖 **Generation** — RAG-powered Q&A, summarization, comparison
- 💬 **Chat** — Session-based conversational RAG
- 🌐 **Web UI** — Beautiful chat interface
- 📚 **Swagger** — Interactive API documentation

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         FastAPI App                              │
├─────────────────────────────────────────────────────────────────┤
│  /spaces    /artifacts    /chunks    /vectors    /retrieve      │
│  /generate  /chat                                                │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│   ┌──────────────┐    ┌──────────────┐    ┌──────────────┐      │
│   │   Chunker    │───▶│  Embeddings  │───▶│   LanceDB    │      │
│   │  (Markdown)  │    │ (MiniLM-L6)  │    │ (Vector DB)  │      │
│   └──────────────┘    └──────────────┘    └──────────────┘      │
│                                                   │              │
│                              ┌────────────────────┘              │
│                              ▼                                   │
│   ┌──────────────┐    ┌──────────────┐    ┌──────────────┐      │
│   │   Answer     │◀───│    Ollama    │◀───│  Retrieval   │      │
│   │              │    │(qwen2.5:1.5b)│    │   (Hybrid)   │      │
│   └──────────────┘    └──────────────┘    └──────────────┘      │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🚀 Quick Start

### Prerequisites

- **Python 3.10+**
- **Ollama** — For running local LLMs

### Step 1 — Clone the repository

```bash
git clone https://github.com/your-username/rag-summarizer.git
cd rag-summarizer
```

### Step 2 — Run the setup script

The setup script handles everything: copies `.env`, creates directories, installs dependencies, pulls the Ollama model, starts Ollama, and launches the server.

**Mac / Linux:**
```bash
chmod +x setup.sh
./setup.sh
```

**Windows:**
```bat
./setup.bat
```

> **Windows note:** Ollama must be installed manually before running the script — download from [ollama.com/download](https://ollama.com/download).

---

### Running manually (without the script)

If you prefer to run each step yourself:

```bash
# 1. Copy environment file
cp .env.example .env          # Mac / Linux
copy .env.example .env        # Windows

# 2. Create required directories
mkdir -p fs/plaintables fs/vector_stores uploads    # Mac / Linux
mkdir fs\plaintables fs\vector_stores uploads       # Windows

# 3. Install Python dependencies
pip install -r requirements.txt

# 4. Pull the Ollama model
ollama pull qwen2.5:1.5b

# 5. Start Ollama server (keep this terminal open)
ollama serve

# 6. In a new terminal — start the app

# Accessible only on this machine (localhost):
uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload

# Accessible on your local network (other devices can connect):
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### Access

- **Web UI**: http://localhost:8000
- **Swagger Docs**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

---

## 📖 Usage Guide

### Step 1: Create a Space

```bash
curl -X POST http://localhost:8000/spaces \
  -H "Content-Type: application/json" \
  -d '{"name": "My Project", "description": "Project documentation"}'
```

### Step 2: Upload Documents

```bash
curl -X POST http://localhost:8000/spaces/{space_uuid}/artifacts \
  -F "files=@README.md" \
  -F "files=@docs/guide.md" \
  -F "chunk_strategy=recursive"
```

### Step 3: Generate Embeddings

```bash
curl -X POST http://localhost:8000/spaces/{space_uuid}/vectors/embed \
  -H "Content-Type: application/json" \
  -d '{}'
```

### Step 4: Start Chatting

```bash
# Create a chat session
curl -X POST http://localhost:8000/spaces/{space_uuid}/chat/sessions \
  -H "Content-Type: application/json" \
  -d '{"name": "My Chat"}'

# Send a message
curl -X POST http://localhost:8000/spaces/{space_uuid}/chat/sessions/{session_id} \
  -H "Content-Type: application/json" \
  -d '{"message": "How does authentication work?"}'
```

---

## 📡 API Reference

### Spaces

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/spaces` | Create space |
| `GET` | `/spaces` | List spaces |
| `GET` | `/spaces/{uuid}` | Get space |
| `DELETE` | `/spaces/{uuid}` | Delete space |

### Artifacts

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/spaces/{uuid}/artifacts` | Upload files |
| `GET` | `/spaces/{uuid}/artifacts` | List artifacts |
| `GET` | `/spaces/{uuid}/artifacts/{id}` | Get artifact |
| `DELETE` | `/spaces/{uuid}/artifacts/{id}` | Delete artifact |

### Chunks

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/spaces/{uuid}/chunks` | Create chunk |
| `GET` | `/spaces/{uuid}/chunks` | List chunks |
| `GET` | `/spaces/{uuid}/chunks/{id}` | Get chunk |
| `PUT` | `/spaces/{uuid}/chunks/{id}` | Update chunk |
| `DELETE` | `/spaces/{uuid}/chunks/{id}` | Delete chunk |
| `POST` | `/spaces/{uuid}/chunks/search` | FTS search |

### Vectors

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/spaces/{uuid}/vectors/embed` | Embed chunks |
| `POST` | `/spaces/{uuid}/vectors` | Create vector |
| `GET` | `/spaces/{uuid}/vectors` | List vectors |
| `PUT` | `/spaces/{uuid}/vectors/{id}` | Re-embed |
| `DELETE` | `/spaces/{uuid}/vectors/{id}` | Delete vector |

### Retrieval

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/spaces/{uuid}/retrieve` | Main retrieve |
| `GET` | `/spaces/{uuid}/retrieve/vector?q=` | Vector search |
| `GET` | `/spaces/{uuid}/retrieve/fts?q=` | FTS search |
| `GET` | `/spaces/{uuid}/retrieve/hybrid?q=` | Hybrid search |

### Generation

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/spaces/{uuid}/generate` | RAG Q&A |
| `POST` | `/spaces/{uuid}/generate/summarize` | Summarize |
| `POST` | `/spaces/{uuid}/generate/compare` | Compare docs |

### Chat

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/spaces/{uuid}/chat/sessions` | Create session |
| `GET` | `/spaces/{uuid}/chat/sessions` | List sessions |
| `GET` | `/spaces/{uuid}/chat/sessions/{id}` | Get session |
| `DELETE` | `/spaces/{uuid}/chat/sessions/{id}` | Delete session |
| `POST` | `/spaces/{uuid}/chat/sessions/{id}` | Send message |
| `GET` | `/spaces/{uuid}/chat/sessions/{id}/history` | Get history |

---

## 📁 Project Structure

```
rag-summarizer/
├── app/
│   ├── main.py              # FastAPI entry point
│   ├── core/
│   │   ├── config.py        # Settings
│   │   ├── database.py      # LanceDB managers
│   │   └── embeddings.py    # Sentence Transformers
│   ├── utils/
│   │   └── chunker.py       # Chunking strategies
│   ├── spaces/              # Space management
│   ├── artifacts/           # File upload
│   ├── chunks/              # Chunk CRUD + FTS
│   ├── vectors/             # Embedding + vectors
│   ├── retrieval/           # Search (vector/FTS/hybrid)
│   ├── generation/          # LLM generation
│   └── chat/                # Session-based chat
├── fs/
│   ├── plaintables/         # LanceDB plain tables
│   └── vector_stores/       # LanceDB vector stores
├── static/
│   └── index.html           # Web chat UI
├── uploads/                 # Temp upload folder
├── requirements.txt
├── setup.sh             # One-shot setup (Mac / Linux)
├── setup.bat            # One-shot setup (Windows)
├── .env.example
└── README.md
```

---

## ⚙️ Configuration

Copy `.env.example` to `.env` and customize (Mac/Linux: `cp .env.example .env`, Windows: `copy .env.example .env`):

```bash
# Server
HOST=0.0.0.0
PORT=8000
DEBUG=true

# Storage
PLAINTABLES_PATH=./fs/plaintables
VECTOR_STORES_PATH=./fs/vector_stores
UPLOADS_PATH=./uploads

# Embeddings
EMBEDDING_MODEL=all-MiniLM-L6-v2

# LLM (Ollama)
OLLAMA_HOST=http://localhost:11434
OLLAMA_MODEL=qwen2.5:1.5b

# Chunking
CHUNK_SIZE=500
CHUNK_OVERLAP=50
```

---

## 🧩 Chunking Strategies

| Strategy | Description | Best For |
|----------|-------------|----------|
| `fixed_size` | Split every N characters | Uniform processing |
| `paragraph` | Split by double newlines | Articles, blogs |
| `sentence` | Group N sentences | Q&A, precise retrieval |
| `markdown_header` | Split by # headers | README, documentation |
| `recursive` | Smart multi-level split | General purpose ✨ |

---

## 🔍 Retrieval Modes

| Mode | Description | When to Use |
|------|-------------|-------------|
| `vector` | Semantic similarity | "Find similar concepts" |
| `fts` | Keyword matching | "Find exact terms" |
| `hybrid` | Combined (recommended) | Best of both worlds |

---

## 🛠️ Common Commands

| Task | Mac / Linux | Windows |
|------|-------------|---------|
| Install dependencies | `pip install -r requirements.txt` | `pip install -r requirements.txt` |
| Setup `.env` | `cp .env.example .env` | `copy .env.example .env` |
| Create directories | `mkdir -p fs/plaintables fs/vector_stores uploads` | `mkdir fs\plaintables fs\vector_stores uploads` |
| Dev server (reload) | `uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload` | same |
| Production server | `uvicorn app.main:app --host 0.0.0.0 --port 8000` | same |
| Pull Ollama model | `ollama pull qwen2.5:1.5b` | same |
| Clean generated files | `rm -rf fs/plaintables/* fs/vector_stores/* uploads/*` | `del /q fs\plaintables\* fs\vector_stores\* uploads\*` |

---

## 📚 Tech Stack

| Component | Technology |
|-----------|------------|
| **Framework** | FastAPI |
| **Vector DB** | LanceDB |
| **Embeddings** | Sentence Transformers (all-MiniLM-L6-v2) |
| **LLM** | Ollama + qwen2.5:1.5b |
| **Storage** | Plain tables + Vector stores |

---

## 🔧 Troubleshooting

### "Ollama not running"

```bash
# Start Ollama server
ollama serve

# In another terminal, check it's running
curl http://localhost:11434/api/tags
```

### "Model not found"

```bash
ollama pull qwen2.5:1.5b
```

### "No embeddings found"

Make sure to embed chunks after uploading:

```bash
curl -X POST http://localhost:8000/spaces/{uuid}/vectors/embed
```

### "FTS not working"

FTS index is created automatically on first search. Make sure you have chunks uploaded.

---

## 🚧 Roadmap

- [ ] Support more file types (PDF, DOCX)
- [ ] Multi-language support
- [ ] Streaming responses
- [ ] Authentication
- [ ] Docker deployment
- [ ] Evaluation metrics

---

## 🙏 Acknowledgments

- [FastAPI](https://fastapi.tiangolo.com/) — Modern Python web framework
- [LanceDB](https://lancedb.com/) — Excellent embedded vector database
- [Ollama](https://ollama.com/) — Making local LLMs accessible
- [Sentence Transformers](https://sbert.net/) — Great embedding models

---

## 📄 License

MIT License — feel free to use for learning and building!

---

Built with ❤️ for the **"Bootstrap of RAG"** workshop

**Questions?** Open an issue or reach out during the workshop!
