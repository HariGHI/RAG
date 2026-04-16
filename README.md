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
│   │              │    │  (Llama 3.2) │    │   (Hybrid)   │      │
│   └──────────────┘    └──────────────┘    └──────────────┘      │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🚀 Quick Start

### Prerequisites

- **Python 3.10+**
- **Ollama** — For running local LLMs


### Installation

```bash
# 1. Clone the repository
git clone https://github.com/your-username/rag-summarizer.git
cd rag-summarizer

# 2. Setup environment
make setup

# 3. Install dependencies
make install

# 4. Install and start Ollama
curl -fsSL https://ollama.com/install.sh | sh
ollama pull llama3.2
ollama serve  # Keep this running in a separate terminal

# 5. Start the server
make dev
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
├── Makefile
├── .env.example
└── README.md
```

---

## ⚙️ Configuration

Copy `.env.example` to `.env` and customize:

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
OLLAMA_MODEL=llama3.2

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

## 🛠️ Makefile Commands

```bash
make install      # Install dependencies
make setup        # Create .env and directories
make dev          # Run dev server (with reload)
make run          # Run production server
make ollama-pull  # Pull Llama 3.2 model
make clean        # Clean generated files
make init         # Full setup (setup + install + ollama)
```

---

## 📚 Tech Stack

| Component | Technology |
|-----------|------------|
| **Framework** | FastAPI |
| **Vector DB** | LanceDB |
| **Embeddings** | Sentence Transformers (all-MiniLM-L6-v2) |
| **LLM** | Ollama + Llama 3.2 |
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
ollama pull llama3.2
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
