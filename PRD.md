# PRD: JWRAG

## Problem Statement
Professionals managing sensitive and confidential documents lack a secure, private way to query their repository and synthesize complex, multi-document insights. Current mainstream RAG solutions rely heavily on cloud-hosted infrastructure, which introduces unacceptable data privacy risks for confidential text. Furthermore, standard QA systems focus on retrieving single, flattened answers, failing to provide the varied analytical perspectives or "alternative judgments" necessary for robust decision-making.

## Objectives and Success Metrics

**Objectives**:

* Deliver a 100% localized, air-gapped RAG environment that guarantees zero data egress.

* Automate repository management so the user never has to manually re-index altered files.

* Provide a decision-support system that synthesizes multiple sources into distinct, actionable options.

**Success Metrics**:

* Privacy Verification: Absolute zero external network requests triggered during indexing or execution.

* Synchronization Accuracy: 100% of document creations, modifications, and deletions are accurately reflected in the search index without manual intervention.

* Synthesis Compliance: Every qualified query successfully yields multiple independent judgment options alongside clear, unambiguous file citations.

## Scope (In / Out)

**In Scope**:

* Monitoring a single, local raw document directory for file changes.

* Local embedding generation and vector space storage.

* A synthesis engine capable of evaluating cross-document references to produce multiple distinct perspectives.

* A lightweight, clean Terminal User Interface (TUI) for interactive querying.

* Rigid enforcement of Specification Driven Development (SDD) and Test-Driven Development (TDD) methodologies throughout construction.

**Out of Scope**:

* Cloud storage integration (S3, Google Drive, etc.) or multi-user network access.

* Optical Character Recognition (OCR) for scanned images or non-selectable PDFs.

* Granular user access controls or Role-Based Access Control (RBAC).


## Users & Use Cases

**Primary User**: local user working with highly sensitive, proprietary data layers who require private, offline decision-making support.

**Use Cases**:

* Real-time Document Updates: A user edits a local polic; the system detects the update and seamlessly modifies the index in the background.

* Cross-Document Synthesis: A user queries a complex scenario spanning multiple separate policy documents. Instead of a single response, the system presents two or three distinct scenarios (e.g., a conservative option vs. a progressive option) based on the combined data to assist in decision making.

* Audit Trails: A user reviews the generated options and instantly verifies the source material via explicit, appended filenames in the terminal.


## Requirements

### 1. Local Document Repository & Vector Database
* The system must operate exclusively within a user-defined local folder.

* The vector store and its embeddings must be initialized, written, and read entirely from the local machine.

* The system must support standard text-based formats (such as .txt, .md, and searchable .pdf).

### 2. Automated Incremental Synchronization
* The pipeline must actively watch the raw document directory for file events.

* New Files: Automatically chunked and added to the index upon detection.

* Modified Files: Automatically re-indexed by purging old vector blocks linked to that document identity and updating them with new content.

* Deleted Files: Corresponding vector footprints must be completely purged from the database immediately.

### 3. "Exercise Judgment" Engine
* The querying mechanism must be capable of aggregating context chunks from multiple documents simultaneously.

* The engine must process the aggregated text to output multiple distinct options or conclusions (minimum of 2) rather than a single unified answer, framing the information from different analytical angles.

### 4. Interactive Terminal UI (TUI)
* The interface must be a straightforward interactive command-line environment.

* Outputs must follow a strict layout: the user’s query, the structured alternative judgment options, and a standalone references section explicitly listing the names of the source documents.

### Constraints
* Hardware and Environment: Must execute natively on a local workstation without relying on cloud-based API keys or network availability.

* Methodology: Full system build is gated by the creation of a SPEC.md contract. All underlying modules must be built utilizing a strict TDD loop (tests written and failing prior to feature implementation).

* Target: the application targets repositories of ~500 pdf documents or less which amounts to a rough 10,000 chunks or less. 


## Acceptance Criteria

* Dropping a new file into the repository updates the search index automatically without a restart, and deleting it removes it from search results entirely.

* Queries analyzing overlapping source text output multiple clear, non-identical judgment options.

* Every terminal response lists the correct, un-hallucinated file names of the referenced documents.

* The entire pipeline passes a local network traffic audit, demonstrating perfectly air-gapped execution during indexing and inference tasks.