# Plan: Replace FAISS Vector Memory with File-Based Memory

## Context

The current memory system uses FAISS vector indices + sentence-transformers embeddings for semantic search. This pulls in ~1.5GB of dependencies (torch, transformers, faiss-cpu, sentence-transformers) that are too heavy for Raspberry Pi deployment. We replace it with a pure-Python JSON file store + TF-IDF keyword search — zero ML dependencies, same public API.

## Scope

- **Long-term memory** (save/load/delete/forget tools, recall, memorization, consolidation) — fully replaced
- **Short-term memory and rest of system** — unaffected (extensions, agent loop, prompts all untouched)
- **DocumentQueryStore** (`document_query.py`) — its `VectorDB` dependency also rewritten (same TF-IDF approach, ephemeral in-memory)
- **Dead code cleanup** — embedding pipeline, FAISS monkey patch, unused deps removed

---

## Changes (in execution order)

### 1. Create `python/helpers/tfidf.py` (NEW FILE)

Pure-Python TF-IDF search engine. No external dependencies.

- `tokenize(text) -> list[str]` — lowercase, split on non-alphanumeric, filter stopwords
- `compute_tfidf_vectors(corpus: dict[str, list[str]]) -> (vectors, idf)` — build TF-IDF vectors for all docs
- `tfidf_query_vector(query_tokens, idf) -> Counter` — vectorize a query
- `cosine_similarity(vec_a, vec_b) -> float` — sparse vector cosine
- `search(query, corpus_vectors, idf, limit, threshold) -> list[(doc_id, score)]` — main search function

Uses only: `math`, `re`, `collections.Counter`.

### 2. Rewrite `python/helpers/memory.py`

**Remove**: all FAISS/embedding imports (`faiss`, `faiss_monkey_patch`, `FAISS`, `CacheBackedEmbeddings`, `LocalFileStore`, `InMemoryByteStore`, `InMemoryDocstore`, `DistanceStrategy`, `Embeddings`, `numpy`, embedding model usage from `models`).

**Keep**: `langchain_core.documents.Document`, `simpleeval`, `guids`, `files`, `knowledge_import`, `Log/LogItem`, `PrintStyle`, `Enum`, `Agent/AgentContext`.

**Add**: `from python.helpers.tfidf import tokenize, compute_tfidf_vectors, search as tfidf_search`

**Structural changes**:

| Current | New |
|---------|-----|
| `MyFaiss(FAISS)` subclass | Deleted — no FAISS wrapper needed |
| `Memory.index: dict[str, MyFaiss]` | `Memory.index: dict[str, Memory]` — caches Memory instances directly |
| `Memory.__init__(db: MyFaiss, memory_subdir)` | `Memory.__init__(docs: dict[str, Document], memory_subdir)` |
| Storage: `index.faiss` + `index.pkl` | Storage: `memory.json` |
| `Memory.initialize(log_item, model_config, memory_subdir, in_memory)` | `Memory.initialize(log_item, memory_subdir, in_memory)` — no `model_config` |
| Search via FAISS `asearch(similarity_score_threshold)` | Search via `tfidf_search()` + metadata filter |

**Instance fields**:
- `self.docs: dict[str, Document]` — all documents keyed by ID
- `self.memory_subdir: str`
- `self._tfidf_vectors: dict[str, Counter]` — cached TF-IDF vectors
- `self._idf: dict[str, float]` — cached IDF weights
- `self._tfidf_dirty: bool` — recompute flag, set True on any mutation

**Backward compatibility for `memory_consolidation.py`**:
The consolidation code calls `db.db.get_by_ids()` and `db.db.aget_by_ids()` (4 call sites at lines 164, 295, 645, 730). Fix by adding `self.db = self` alias in `__init__` and implementing `get_by_ids(ids)` / `aget_by_ids(ids)` methods that do dict lookups.

**JSON storage format** (`memory.json`):
```json
{
  "doc_id_1": {"page_content": "...", "metadata": {"id": "doc_id_1", "area": "main", "timestamp": "..."}}
}
```

**`get_existing_memory_subdirs()`**: Change detection from `index.faiss` to `memory.json`.

**All public methods preserved with same signatures**:
- `get(agent)`, `get_by_subdir(memory_subdir, ...)`, `reload(agent)`, `initialize(...)`
- `search_similarity_threshold(query, limit, threshold, filter)`
- `insert_text(text, metadata)`, `insert_documents(docs)`, `update_documents(docs)`
- `delete_documents_by_ids(ids)`, `delete_documents_by_query(query, threshold, filter)`
- `get_document_by_id(id)`, `format_docs_plain(docs)`, `get_timestamp()`
- All utility functions: `abs_db_dir()`, `abs_knowledge_dir()`, `get_agent_memory_subdir()`, etc.

**Remove**: `_score_normalizer()`, `_cosine_normalizer()` (dead code), `_save_db_file()` static method (replaced by instance `_save_db()`).

### 3. Rewrite `python/helpers/vector_db.py`

Ephemeral in-memory store for `document_query.py`. Same TF-IDF approach, not persisted.

**Remove**: all FAISS/embedding imports.
**Keep**: `Document`, `simpleeval`, `guids`.

**Constructor**: `VectorDB(agent, cache=True)` — accept `cache` kwarg for backward compat but ignore it (no embeddings to cache).

**Methods preserved**:
- `search_by_similarity_threshold(query, limit, threshold, filter)` — TF-IDF search
- `search_by_metadata(filter, limit)` — iterate docs, apply simpleeval comparator
- `insert_documents(docs)` — add to dict, mark TF-IDF dirty
- `delete_documents_by_ids(ids)` — remove from dict
- `get_all_docs()` — return docs dict

**Keep**: `format_docs_plain()`, `get_comparator()`.
**Remove**: `cosine_normalizer()` (unused).

### 4. Delete `python/helpers/faiss_monkey_patch.py`

Only existed for FAISS ARM64 compatibility. No longer needed.

### 5. Clean up `models.py`

**Remove** (lines 670-810):
- `LiteLLMEmbeddingWrapper` class (lines 670-702)
- `LocalSentenceTransformerWrapper` class (lines 705-752)
- `_get_litellm_embedding()` function (lines 777-810)
- `get_embedding_model()` function (lines 924-929)

**Remove imports** (lines 42-43):
- `from langchain.embeddings.base import Embeddings`
- `from sentence_transformers import SentenceTransformer`

### 6. Clean up `agent.py`

- **Remove** `embeddings_model: models.ModelConfig` from `AgentConfig` dataclass (line 302)
- **Remove** `Agent.get_embedding_model()` method (lines 754-760)

### 7. Clean up `initialize.py`

- **Remove** `embedding_llm` ModelConfig construction (lines 57-64)
- **Remove** `embeddings_model=embedding_llm` from AgentConfig constructor (line 78)

### 8. Clean up `preload.py`

- **Remove** the `preload_embedding()` function and its entry in the tasks list (lines 20-30, 42)
- Keep whisper and kokoro preloads

### 9. Clean up `python/helpers/settings.py`

- **Remove** the embedding model change detection block that triggers memory reload (lines 626-634) — embeddings no longer exist, memory reload is no longer coupled to embedding model changes
- **Keep** the `embed_model_*` settings fields in the TypedDict — removing them would break existing `usr/settings.json` files. They become inert.

### 10. Clean up `requirements.txt`

**Remove**:
- `faiss-cpu==1.11.0` (line 6)
- `sentence-transformers==3.0.1` (line 29) — this also drops transitive deps: `torch` (~800MB), `transformers`, `huggingface-hub`

**Keep**: `langchain-core`, `langchain-community` (used for Document, messages, document loaders), `simpleeval`.

### 11. Migration script `scripts/migrate_faiss_to_json.py` (NEW FILE)

One-time migration for existing FAISS data. Must be run **before** removing faiss-cpu from the environment.

- Scans `usr/memory/*/index.faiss` and project memory folders
- Loads each FAISS index via LangChain's `FAISS.load_local()`
- Extracts all Documents from the InMemoryDocstore
- Writes `memory.json` in the same directory
- Prints summary of migrated subdirs

Fallback: `Memory.initialize()` detects `index.faiss` without `memory.json` and logs a warning with migration instructions.

---

## What stays untouched

- All 4 memory tools (`memory_save.py`, `memory_load.py`, `memory_delete.py`, `memory_forget.py`) — they call Memory public API only
- All memory extensions (`_10_memory_init.py`, `_50_recall_memories.py`, `_50_memorize_fragments.py`, `_51_memorize_solutions.py`)
- `memory_consolidation.py` — uses Memory public API (with `db.db` alias fix)
- `memory_dashboard.py` API
- `document_query.py` — uses VectorDB public API (unchanged signatures)
- `knowledge_import.py` — produces Documents consumed by Memory, no FAISS dependency
- All prompts, agent profiles, short-term memory, agent loop

---

## Search quality note

TF-IDF is keyword-based, not semantic. "Fix SSH issue" won't match "Repair secure shell problem." Mitigations:
1. The system already uses LLM-generated search queries (in recall extension and consolidation), producing keyword-rich queries
2. Memory consolidation uses LLM keyword extraction before search
3. For the hacker-rpi use case, security terms are highly keyword-specific (CVE IDs, tool names, IP addresses)

---

## Verification

1. **Unit test `tfidf.py`**: tokenization, search ranking, threshold filtering, empty corpus
2. **Integration test Memory CRUD**: insert → search → update → delete cycle
3. **Test memory tools**: `memory_save` → `memory_load` → `memory_delete` → `memory_forget`
4. **Test consolidation**: verify `memory_consolidation.py` works with new Memory (especially `db.db.get_by_ids()` alias)
5. **Test document_query**: verify `DocumentQueryStore` with new `VectorDB`
6. **Dependency check**: confirm no FAISS/torch imports remain; `pip install` on clean env
7. **Run existing tests**: `pytest tests/`
