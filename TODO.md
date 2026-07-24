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
- [x] **Interface**: Define `IDocumentParser` abstract base class.
- [x] **Test**: Write tests for Text/Markdown parsing.
- [x] **Implement**: Build Text/Markdown parser.
- [x] **Test**: Write tests for searchable PDF parsing (using `pypdf`).
- [x] **Implement**: Build PDF parser.
- [x] **Test**: Write tests for chunking logic (1024 char size, 150-200 char overlap, hierarchical separators).
- [x] **Implement**: Build text chunker.

## Phase 4: Embedding & Synthesis Engine
- [x] **Interface**: Define `ISynthesisEngine` abstract base class.
- [x] **Test**: Write tests for Ollama embedding client (mocking HTTP requests).
- [x] **Implement**: Build Ollama embedding client targeting `/api/embeddings` (using `qwen3-embedding:4b` or `bge-me:latest`).
- [x] **Test**: Write tests for NumPy-based Cosine Similarity vector search.
- [x] **Implement**: Add vector search logic to `SQLiteVectorStore`.
- [x] **Test**: Write tests for the LLM synthesis pipeline (mocking Ollama JSON responses and malformed responses).
- [x] **Implement**: Build LLM prompt construction and query execution (targeting `gemma4:26b-mlx`).
- [x] **Implement**: Build robust JSON parsing pipeline (Direct Parse -> Markdown Stripping -> Regex -> Retry Loop -> Hard Fallback).

## Phase 5: Directory Synchronization Pipeline
- [x] **Interface**: Define `IDirectoryWatcher` abstract base class.
- [x] **Test**: Write tests for file hashing and change detection logic.
- [x] **Implement**: Build `IndexSyncManager` (comparing hashes, triggering Insert/Delete sequences).
- [x] **Test**: Write tests for `watchdog` event translation (mocking file system events).
- [x] **Implement**: Build `DirectoryWatcher` using `watchdog`.

## Phase 6: Terminal User Interface (TUI) & Integration
- [x] **Test**: Write tests for formatting TUI outputs (Query, Judgment Options, References).
- [x] **Implement**: Build interactive CLI for accepting user queries and rendering `SynthesisResult` gracefully.
- [x] **Integrate**: Connect TUI with `ISynthesisEngine` and `IVectorStore`.
- [x] **Integrate**: Run `DirectoryWatcher` alongside the TUI.
- [x] **Audit**: Verify zero data egress (air-gapped execution) and correct file citations.

## Phase 7: Final Pipeline Integration
- [x] **Test**: Write `test_main.py` for integration testing.
- [x] **Implement**: Connect the full parsing and embedding pipeline in `sync_callback` inside `main.py`.
- [x] **Implement**: Complete the execution pipeline in `process_query` inside `main.py`.

## Phase 8: Cloud Integration & Data Security
- [x] **Config**: Implement configuration system (`.env` or `config.yaml`) for routing between local and cloud models.
- [x] **Test**: Write tests for the Data Sanitization pipeline (verifying PII removal and restoration).
- [x] **Implement**: Build `DataSanitizer` using Presidio/SpaCy.
- [x] **Test**: Write tests for `CloudSynthesisEngine` (mocking OpenAI/Anthropic APIs).
- [x] **Implement**: Build `CloudSynthesisEngine` implementing `ISynthesisEngine`.
- [x] **Integrate**: Wire configuration to select the correct engine in `main.py`.

## Phase 9: Detailed Judgment References Feature
- [x] **Test**: Write tests for `Reference` DTO and updated `SynthesisResult`.
- [x] **Implement**: Update DTOs to include `Reference` object with `page` and `paragraph`.
- [x] **Test**: Write tests for extracting paragraph identifiers in document parsers and chunking logic.
- [x] **Implement**: Modify document parsers and chunking logic to extract and tag chunks with paragraph identifiers.
- [x] **Test**: Write tests for context block prefixing and parsing the new `references` output from LLM.
- [x] **Implement**: Modify `ISynthesisEngine` implementations to prefix context blocks with metadata and parse detailed `references`.
- [ ] **Test**: Write tests for formatting the detailed references section in the TUI output.
- [ ] **Implement**: Update TUI formatting to display the detailed references cleanly at the bottom of the output.
