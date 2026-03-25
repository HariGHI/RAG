# RAG Pipeline Flow

## Phase 1 — Upload & Chunk

**Endpoint:** `POST /spaces/{space_uuid}/artifacts/upload`

1. **Validate** — space must exist; file must be `.md`, `.markdown`, or `.txt`
2. **Read file** — decoded as UTF-8 string
3. **Chunk** (`app/utils/chunker.py`) — strips YAML frontmatter, protects code blocks, then applies the chosen strategy (default: `recursive` -> `semantic`):
   - Parses markdown into sections with header hierarchy (`title`, `parent_title`, `level`)
   - Keeps small sections whole; splits large ones at paragraph -> sentence boundaries with overlap
4. **Store chunks** (`app/artifacts/service.py`) — each chunk gets a UUID and is inserted into LanceDB's **plain table** (with FTS index)

---

## Phase 2 — Embed (separate step)

**Endpoint:** `POST /spaces/{space_uuid}/vectors/embed`

5. **Load chunks** from plain table
6. **Generate embeddings** (`app/core/embeddings.py`) — uses `all-MiniLM-L6-v2` (384-dim) via SentenceTransformers in batch
7. **Store vectors** — inserted into LanceDB's **vector store table**

---

## Phase 3 — Retrieval

**Endpoint:** `POST /spaces/{space_uuid}/retrieve`

8. **Retrieve** (`app/retrieval/service.py`) based on mode:
   - **`vector`** — embeds query -> ANN search on vector store -> L2 distance converted to similarity score
   - **`fts`** — keyword search on plain table's FTS index
   - **`hybrid`** — both combined via LanceDB's hybrid search
9. Returns top-k chunks with scores and ranks

---

## Phase 4 — Augmentation

**Endpoint:** `POST /spaces/{space_uuid}/augment` (optional inspection step)

10. **Build context string** (`app/augmentation/service.py`) — formats chunks with breadcrumb (`file > parent_title > title`)
11. **Build prompt messages** — system prompt + user prompt in format:
    ```
    Context: <retrieved chunks>
    Question: <query>
    Answer based on the context above:
    ```

---

## Phase 5 — Generation / Answer

**Endpoint:** `POST /spaces/{space_uuid}/generate`

12. **Retrieve + Augment** (internally calls both steps)
13. **Generate** (`app/generation/service.py`) — sends messages to **Ollama** (`ollama.chat`) with the augmented prompt
14. Returns `answer` + `sources` (chunk previews with file names)

---

## Alternative: Chat (multi-turn)

**Endpoint:** `POST /spaces/{space_uuid}/chat/sessions/{session_id}`

Same as generation but also:
- Prepends **last 10 messages** of conversation history to the prompt
- Saves user + assistant messages to a JSON session file after each turn

---

## Summary Diagram

```
File Upload
    |
    v
Chunker (semantic/recursive)
    |  strips frontmatter, preserves code blocks
    |  tracks title hierarchy
    v
Plain Table (LanceDB + FTS index)
    |
    v  [/vectors/embed]
EmbeddingModel (all-MiniLM-L6-v2)
    |
    v
Vector Store (LanceDB)

─────── Query time ───────

Query
    |
    v  [/retrieve]
Retrieval (vector / FTS / hybrid)
    |
    v  [/augment]
Augmentation (context string + prompt)
    |
    v  [/generate]
Ollama LLM -> Answer
```
