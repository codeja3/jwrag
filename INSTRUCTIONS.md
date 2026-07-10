# INSTRUCTIONS.md: JWRAG & AI Standards

This document defines the immutable rules of engagement for developing JWRAG. It governs both the architectural design of the software and the collaborative workflow between the developer and the AI assistant. 

## 1. Development Workflow & AI Collaboration
* **CLI-Exclusive Execution:** All development, testing, and execution must occur directly via the Command Line Interface (CLI). Workflows tailored for Graphical IDEs (like Jupyter Notebooks or VS Code integrated runners) are strictly prohibited.
* **Spec-Driven Development (SDD):** `SPEC.md` is the ultimate source of truth. System specifications, API contracts, and data schemas must be explicitly defined and locked in `SPEC.md` before pipeline construction begins.
* **Strict Test-Driven Development (TDD):** Tests strictly dictate implementation. For every task, xUnit-style tests must be written and executed *before* any core implementation logic is authored.
* Enforce RED-GREEN-Refactor cycle, with tests written first
* FORBIDDEN: Implementation before test, skipping RED phase
* FORBIDDEN: Changing the tests simply in order to pass. All changes to tests should reflect either a change in requirements or an error identified in the test.
* FORBIDDEN: Simplifying the problem to pass the test.
* **The "Ping-Pong" Protocol:** 
  1. Define task.
  2. AI writes the failing test.
  3. AI executes the test autonomously via CLI to verify it fails (RED), keeping the Developer informed.
  4. AI writes the minimum implementation to pass.
  5. AI executes the test autonomously to verify it passes (GREEN).
  6. Refactor and document.

## 2. Core Design Principles
* **Single Responsibility Principle (SRP):** One module, one class, one job. If a class's purpose cannot be described without using the word "and," it must be split. (e.g., Extract validation logic from extraction logic).
* **Defensive Programming (Fail-Fast):** Validate inputs immediately. Use custom exceptions for validation errors. Do not swallow exceptions; propagate them up or handle them explicitly. 
* **Encapsulation & Abstraction:** Hide internal state. Expose behavior, not data. Protect internal mechanisms from arbitrary modification.
* **Extensibility (Open/Closed):** Code should be open for extension but closed for modification. Use strategy patterns, interfaces, and composition over deep inheritance chains or monolithic `if/else` blocks.
* **Simplicity (KISS, DRY, YAGNI):** Prefer simple solutions. Extract common logic to maintain a single source of truth. Do not build abstractions for hypothetical future needs.  
* **Evaluation of Effectiveness:** Before creating code, brainstorm 5 different approaches to solve the problem and sort them by their probable effectiveness. Then choose the best approach and implement it.

## 3. Language & Environmental Standards

### Python Ecosystem Mandates
* **Cross-Platform Portability:** String concatenation for paths is prohibited. `pathlib` must be used for all file system interactions.
* **Type Safety:** Strict type hints are mandatory for all function signatures and class properties.
* **Docstrings:** Use google style docstrings on each function you are writing. 
* **Data Structures:** Use `dataclasses` (or Pydantic models) for immutable data passing.
* **Resource Management:** Context managers (`with` statements) are mandatory for file I/O and database connections to ensure automatic cleanup.
* **Interface Design:** Use the `abc` module to define clear abstract base classes for swappable components.
* **Script execution:**  use `uv run` to execute Python scripts and commands.   
* **Code testing:**  use `pytest` for testing your code.  
        * **Test fixtures:** Collect pytest fixtures in a conftest.py file to avoid duplication.
* **Logging:** Use logging to provide insight into failures. Don't use print for debugging. Don't use logging to hide stack traces if you are going to fail anyway. Prefer simpler packages for logging where possible such as `loguru` over native logging libraries. 


## 4. Workflow Context (Spec-Driven)
*   **Context Reading:** Before writing code, always read the project's memory files, including the Project Requirements Document (`PRD.md`), specifications (`SPEC.md`), and the active task list (`TODO.md`).
*   **Bounded Execution:** Only implement the specific, bounded task assigned to you. Do not engage in "gold-plating," scope creep, or attempting to solve problems outside the current requirement.

## 5. JWRAG Domain Rules

* **Absolute Privacy:** The system must never make external network calls for data processing. All LLM inference must occur via the local server (Ollama).

## 6. Package Management & Environment
* **No Monolithic Environments:** Monolithic environment managers (like Conda) and full-stack containerization (like Docker) are explicitly rejected to preserve bare-metal hardware access for local LLM inference on Apple Silicon.
* **Python Dependency Management:** `uv` is the mandated package manager for the Python extraction layer. Standard `pyproject.toml` will be used, and execution will occur within a `uv`-managed virtual environment.

## 7. Task Completion & Memory Synchronization Policy
You must strictly follow the "Commit-Clear-Reload" cycle upon completing any discrete task from TODO.md. (Note: "Clear-Reload" means clearing the active AI chat context window to save tokens and starting a fresh session with only `MEMORY.md` and relevant files as the active context).

1. **Verify Completion:** Run the necessary test suites to verify the task is genuinely complete and passing. Do not rely on premature completion claims.
2. **Annotate State:** Immediately update the `TODO.md` file by marking the task as completed. Simultaneously, update the "Active Task Tracker" or "Running Checklist" section inside `MEMORY.md` to reflect this change.
3. **Log Progress/Failures:** - If successful, remove the item from the active scratchpad.
   - If a strategy failed or a specific error workaround was required, annotate it in the `MEMORY.md` scratchpad/error log so the context survives future session clears.
4. **Prepare for Commit:** Generate a detailed, granular commit message summarizing the changes made.

## 8. Git Branching & Lifecycle Policy

You must strictly execute all development tasks inside dedicated feature branches. Never write code directly to the primary branch.

### 1. Phase/Milestone Initialization
Before starting work on a new phase or major milestone defined in TODO.md:
- **Command:** Checkout the primary stable branch, pull the latest changes, and spin up a new branch.
- **Naming Convention:** `feature/phase-[number]-[short-description]` (e.g., `feature/phase-1-jwt-auth`).

### 2. The Step-by-Step Execution Loop
For every discrete sub-task listed under the active phase:
1. **Implement & Test:** Write code to complete exactly *one* task. Run validation scripts or the test suite to guarantee correctness.
2. **Sync Project Memory:** Update `TODO.md` to mark the task complete. If errors occurred or specific workarounds were required, log them in the `MEMORY.md`.
3. **Granular Commit:** Stage the relevant assets and create a commit.
   - **Commit Naming:** Prefix the message with the phase (e.g., `feat(phase-1): implement token serialization`).

### 3. Phase Completion & Merging
Once every task within the active phase is fully verified, checked off, and committed:
1. Review a full `git diff` against the primary branch to scan for unexpected structural code smells or dead code.
2. Check out the primary branch, merge the feature branch cleanly, and push the verified updates up to the remote origin. (Note: Pushing code to a remote is permitted, but ensure that any sample test documents are strictly local and excluded via `.gitignore` to maintain the air-gapped data privacy constraint).
3. Delete the local feature branch to maintain a clean workspace environment.