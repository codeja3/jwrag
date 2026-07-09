# MEMORY.md: JWRAG Context & State

### 1. Core Purpose & Intent
JWRAG is a 100% localized, air-gapped decision support system that watches a local directory of sensitive documents and securely indexes them. Rather than returning flat answers, it synthesizes multi-perspective analytical options (alternative judgments) grounded in verifiable file citations, with absolute guarantees of zero data egress.

### 2. Active Context Pointer & Sub-Files
**AI Directive**: To grasp the full scope of this project, you must ingest the following core contract files:
- **`PRD.md`**: Problem statement, metrics, scope, and user requirements.
- **`SPEC.md`**: System architecture, data design (SQLite schema), LLM modeling (Ollama), and interface definitions.
- **`INSTRUCTIONS.md`**: Strict workflow rules (CLI-exclusive, TDD, SDD, design principles).
- **`TODO.md`**: The complete task breakdown and discrete execution steps.

### 3. Project Guardrails & Architectural Constraints
*   **100% Offline / Air-Gapped**: Zero external network calls. All data, embeddings, and LLM inferences remain local.
*   **Tech Stack**: Python 3.12+, `uv` (package manager), SQLite + NumPy (for vector storage/search), `pypdf`, `watchdog`, and local Ollama (`qwen3-embedding:4b` / `gemma4:26b-mlx`). 
*   **Prohibited Tech**: Monolithic environments (Conda/Docker), complex vector databases (ChromaDB/FAISS), and cloud APIs.
*   **Strict Methodologies**: 
    *   **TDD First**: RED-GREEN-Refactor. Tests strictly dictate implementation. No code without a failing test first.
    *   **Spec-Driven**: `SPEC.md` is the immutable source of truth.
*   **Non-Goals (Out of Scope)**: Cloud integrations, multi-user/RBAC, and OCR for image-based PDFs.

### 4. Running Checklist & Active Task Tracker
*Current Status: Not Started.*

*   [ ] **Phase 1: Project Setup**: `uv` init, `pyproject.toml`, and dependencies installation (`watchdog`, `pypdf`, `httpx`, `pytest`).
*   [ ] **Phase 2: Database & Core DTOs (TDD)**: Implement `dataclasses` and `SQLiteVectorStore`.
*   [ ] **Phase 3: Parsing & Chunking (TDD)**: Build `IDocumentParser` for text/markdown/pdf and text chunker.
*   [ ] **Phase 4: Synthesis Engine (TDD)**: Build local Ollama API wrappers for embeddings and LLM multi-perspective synthesis with strict JSON parsing.
*   [ ] **Phase 5: Directory Sync (TDD)**: Build `watchdog` integration and `IndexSyncManager`.
*   [ ] **Phase 6: Terminal UI (TUI)**: Build and integrate the CLI interface.

### 5. Persistent Scratchpad / Error Log
*(Use this space to track active blockages, temporary configurations, or recurring errors across sessions)*

*   *No active errors or scratchpad notes.*
