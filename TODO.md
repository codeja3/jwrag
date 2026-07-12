# JWRAG Project TODO List

This `TODO.md` defines the execution plan for the JWRAG system. 
**Crucial Reminder**: Strict Test-Driven Development (TDD) is enforced. For every task, xUnit-style tests must be written and executed *before* any core implementation logic is authored.

## Phase 1: Project Setup & Infrastructure
- [x] Initialize Python project using `uv` (no conda/docker).
- [x] Create `pyproject.toml`.
- [x] Add runtime dependencies: `watchdog`, `pypdf`, `httpx`, `loguru`, `numpy`.
- [x] Add dev dependencies: `pytest`, `pytest-mock`.
- [x] Create `conftest.py` for shared `pytest` fixtures.

## Phase 2: Core Data Structures & Database
- [x] **DTOs**: Define immutable `dataclasses` (`DocumentMetadata`, `Chunk`, `SynthesisOption`, `SynthesisResult`).
- [x] **Interface**: Define `IVectorStore` abstract base class.
- [x] **Test**: Write tests for SQLite initialization, upserting documents, deleting documents, and retrieval.
- [x] **Implement**: Build `SQLiteVectorStore` (tables: `documents`, `document_chunks`) storing vectors as BLOBs.

## Phase 3: Document Parsing & Chunking
- [ ] **Interface**: Define `IDocumentParser` abstract base class.
- [ ] **Test**: Write tests for Text/Markdown parsing.
- [ ] **Implement**: Build Text/Markdown parser.
- [ ] **Test**: Write tests for searchable PDF parsing (using `pypdf`).
- [ ] **Implement**: Build PDF parser.
- [ ] **Test**: Write tests for chunking logic (1024 char size, 150-200 char overlap, hierarchical separators).
- [ ] **Implement**: Build text chunker.

## Phase 4: Embedding & Synthesis Engine
- [ ] **Interface**: Define `ISynthesisEngine` abstract base class.
- [ ] **Test**: Write tests for Ollama embedding client (mocking HTTP requests).
- [ ] **Implement**: Build Ollama embedding client targeting `/api/embeddings` (using `qwen3-embedding:4b` or `bge-me:latest`).
- [ ] **Test**: Write tests for NumPy-based Cosine Similarity vector search.
- [ ] **Implement**: Add vector search logic to `SQLiteVectorStore`.
- [ ] **Test**: Write tests for the LLM synthesis pipeline (mocking Ollama JSON responses and malformed responses).
- [ ] **Implement**: Build LLM prompt construction and query execution (targeting `gemma4:26b-mlx`).
- [ ] **Implement**: Build robust JSON parsing pipeline (Direct Parse -> Markdown Stripping -> Regex -> Retry Loop -> Hard Fallback).

## Phase 5: Directory Synchronization Pipeline
- [ ] **Interface**: Define `IDirectoryWatcher` abstract base class.
- [ ] **Test**: Write tests for file hashing and change detection logic.
- [ ] **Implement**: Build `IndexSyncManager` (comparing hashes, triggering Insert/Delete sequences).
- [ ] **Test**: Write tests for `watchdog` event translation (mocking file system events).
- [ ] **Implement**: Build `DirectoryWatcher` using `watchdog`.

## Phase 6: Terminal User Interface (TUI) & Integration
- [ ] **Test**: Write tests for formatting TUI outputs (Query, Judgment Options, References).
- [ ] **Implement**: Build interactive CLI for accepting user queries and rendering `SynthesisResult` gracefully.
- [ ] **Integrate**: Connect TUI with `ISynthesisEngine` and `IVectorStore`.
- [ ] **Integrate**: Run `DirectoryWatcher` alongside the TUI.
- [ ] **Audit**: Verify zero data egress (air-gapped execution) and correct file citations.
