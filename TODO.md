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
- [x] **Test**: Write tests for formatting the detailed references section in the TUI output.
- [x] **Implement**: Update TUI formatting to display the detailed references cleanly at the bottom of the output.

## Phase 10: Dynamic Location Markers Abstraction
- [x] **Test**: Write failing test for `Reference` DTO and parsers (Text/PDF) storing a generic `markers` dictionary instead of hardcoded page/paragraph fields.
- [x] **Implement**: Update `Reference` DTO, chunk metadata, and document parsers to use dynamic dictionaries (e.g. `{"page": "1", "paragraph": "2"}`).
- [x] **Test**: Write failing test for LLM context prefixing and JSON parsing using the generic `markers` structure.
- [x] **Implement**: Update `ISynthesisEngine` implementations to render `[Document: X, Markers: {...}]` and parse the new JSON schema.
- [x] **Test**: Write failing test for TUI renderer outputting dynamic markers.
- [x] **Implement**: Update `cli.py` to loop through `markers` dictionary in the References section.

## Phase 11: PDF Page Labels Alignment
- [x] **Test**: Write failing test in `test_parser.py` that verifies `PdfParser` uses native PDF page labels (extracting them into `markers["page"]`) instead of the absolute page index.
- [x] **Implement**: Update `PdfParser` to extract `reader.page_labels` and apply them.

## Phase 12: Heuristic PDF Page Parsing
- [x] **Test**: Write failing test in `test_parser.py` that verifies `PdfParser` uses a heuristic fallback to parse physical page numbers from text headers/footers if `page_labels` is missing.
- [x] **Implement**: Write `_extract_printed_page_number` using regex matching on first/last text lines and integrate into `PdfParser`.

## Phase 13: Index-Based Page Calibration
- [x] **Test**: Write failing test in `test_parser.py` for automated page offset calculation via topic index scanning.
- [x] **Implement**: Write `_calibrate_page_offset` in `PdfParser` which samples 5-10 terms from the document's subject index (at the end of the file) and cross-references them against absolute text pages to establish an offset.

## Phase 14: Diacritic Citations and Front-Matter Page Calibration
- [x] **Task 14.1 (TDD)**: Native `/PageLabels` Catalog Check and Front-Matter Roman Numeral Offset in `PdfParser`
  - [x] **Test**: Write failing test in `test_parser.py` verifying that when `/PageLabels` catalog is missing from PDF root, synthetic 1..N numbers are ignored in favor of index offset/heuristics, and pages preceding the body page 1 are labeled as Roman numerals (`i`, `ii`, `iii`, etc.).
  - [x] **Implement**: Update `PdfParser` to check `reader.root_object.get("/PageLabels")` and apply Roman numeral formatting to front-matter/pre-offset pages.
- [x] **Task 14.2 (TDD)**: Chapter & Section Heading Extraction in `TextMarkdownParser` and `PdfParser`
  - [x] **Test**: Write failing tests in `test_parser.py` verifying extraction of `chapter` and `section` markers from text/markdown and PDF documents.
  - [x] **Implement**: Add chapter/section regex scanning (`^#+\s+(?:Chapter|Section)\s+`, `^Chapter\s+([0-9IVXLCDM]+)`, `^§\s*([0-9.]+)`, etc.) across parsers and attach to chunk markers.
- [x] **Task 14.3 (TDD)**: Typographic Diacritic Rendering in `TUIRenderer`
  - [x] **Test**: Write failing test in `test_tui.py` for rendering citations with `p.`, `¶`, `§`, and `Ch.`.
  - [x] **Implement**: Update `TUIRenderer.render_references` in `cli.py` to format markers with standard typographic diacritics.
- [x] **Task 14.4 (TDD)**: Synthesis Prompt & Engine Updates
  - [x] **Test**: Write/update tests in `test_ollama_client.py` and `test_cloud_client.py` verifying context block prefixes and prompt instructions include chapter/section and diacritic citation guidance.
  - [x] **Implement**: Update `OllamaSynthesisEngine` and `CloudSynthesisEngine` prompts with chapter/section and diacritic examples.
