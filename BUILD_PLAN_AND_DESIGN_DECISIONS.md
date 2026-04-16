# BUILD_PLAN_AND_DESIGN_DECISIONS

## What we are trying to build

We are building a **local-first document ETL framework** for unstructured and semi-structured documents, starting with expense-related workflows such as invoices, receipts, and proof-of-payment records.

The system should be able to:

- convert PDFs into page images
- run OCR on those images
- classify documents into caller-defined categories
- extract caller-defined fields
- preserve all intermediate outputs as reusable artifacts
- orchestrate these steps through reusable pipelines
- expose the functionality cleanly to external coding agents through `SKILL.md` wrappers

The immediate use case is expense document processing. The broader goal is to create a reusable framework that can later support many other document-processing pipelines without redesigning the core system.

---

## Core idea

The design is based on a strict separation between:

- **Artifacts**: persistent outputs and state
- **Tools**: atomic executable capabilities
- **Pipelines**: reusable workflows over tools
- **Orchestrator**: planner/executor that resolves dependencies and invokes tools
- **`SKILL.md`**: agent-facing invocation and usage instructions

This separation is the main design decision that makes the system modular, extensible, and suitable for future use by Claude Code, Codex, or similar coding agents.

---

## Design decisions we made

## 1. Local-first architecture

We decided the system should run locally and not depend on cloud APIs or vendor-specific services.

Reasons:
- portability
- privacy
- reduced operational complexity
- easier integration into engineering workflows

The implementation may use local LLM runtimes such as Ollama today, but the architecture must remain model-agnostic.

---

## 2. Minimal dependencies

We decided to keep the dependency footprint small.

Current external dependencies are minimal:
- `pymupdf`
- `ollama`

Everything else should use the standard library where practical.

Reasons:
- portability
- easier setup
- less maintenance overhead
- better long-term robustness

---

## 3. Use plain text / markdown outputs instead of forced JSON

We decided not to force the OCR or extraction models to emit JSON.

Reasons:
- smaller local models degrade when over-constrained
- plain text extraction has worked better in practice
- OCR text and extraction text are easier to inspect manually
- JSON validation can be layered later if needed

As a result:
- OCR outputs are stored as `.ocr.txt` or `.ocr.md`
- extraction outputs are stored as `.extract.txt`
- classification outputs are stored as `.classify.txt`

---

## 4. Sidecar artifact design

We decided to store all derived outputs as sidecar files next to their source artifacts.

Examples:
- `invoice_1.ocr.txt`
- `invoice_1.classify.txt`
- `invoice_1.extract.txt`

We also decided to add a metadata sidecar for each artifact:
- `invoice_1.ocr.txt.meta.json`
- `invoice_1.classify.txt.meta.json`
- `invoice_1.extract.txt.meta.json`

Reasons:
- preserves raw outputs
- keeps derivations inspectable
- simplifies debugging
- avoids mutating source files
- avoids unstable renaming strategies
- supports artifact reuse and staleness detection
- makes future orchestration simpler

Metadata sidecars should live in the **same directory as the artifact they describe**.

---

## 5. Prefer OCR artifacts as reusable intermediates

We decided that downstream tools should prefer OCR sidecars when they exist, and only fall back to the original image if OCR is missing.

Examples:
- classification should prefer `.ocr.txt` / `.ocr.md`
- extraction should prefer `.ocr.txt` / `.ocr.md`

Reasons:
- reduces repeated vision calls
- makes reruns cheaper
- improves modularity
- creates a stable intermediate representation that multiple downstream tools can consume

This is a foundational design choice for later expansion.

---

## 6. Separate OCR, classification, and extraction into independent tools

We decided that OCR, classification, and extraction should remain separate atomic units.

These are **Tools**, not monolithic stages.

Initial tools:
- `pdf_to_image`
- `ocr`
- `classify`
- `extract`

Reasons:
- single responsibility
- easier testing
- better reuse
- simpler orchestration
- easier exposure to external agents
- avoids coupling prompt logic and execution flow together

---

## 7. Keep prompts centralized

We decided all system prompts should live in a dedicated `system_prompts.py` module.

Reasons:
- easier maintenance
- easier experimentation
- prevents prompt logic from being scattered across modules
- keeps business logic cleaner

This also makes it easier to later version prompt presets or swap prompt strategies.

---

## 8. Use an orchestrator instead of a monolithic app flow

We decided that the main application should evolve into a **thin orchestrator**, not a large hardcoded workflow controller.

The orchestrator should:
- inspect available artifacts
- determine what is missing
- resolve dependencies
- invoke the right tool
- register produced artifacts
- stop when the goal is satisfied or no further progress is possible

The orchestrator should **not**:
- contain OCR logic
- contain classification logic
- contain extraction logic
- embed prompt-specific behavior
- rely on fuzzy LLM planning for basic control flow

This is essentially a thin deterministic agentic framework.

---

## 9. Use pipelines for reusable workflows

We decided that reusable workflows should be represented as **Pipelines**.

A pipeline is a named workflow built out of tools and dependencies.

Examples:
- `convert_document`
- `ocr_document`
- `classify_document_type`
- `extract_fields`
- `process_document`
- `process_expense_folder`
- `extract_invoice_fields`

Pipelines are basically structured dependency graphs over tools.

Reasons:
- avoids hardcoded if/else orchestration
- improves reuse
- makes workflows inspectable
- supports conditional execution later
- allows future external YAML definitions

---

## 10. Start with Python dict/dataclass pipeline definitions, then move to YAML

We decided the best implementation path is:

### phase 1
- define pipelines in Python dicts or dataclasses

### phase 2
- move stable pipeline definitions into YAML

Reasons:
- Python is easier while the design is still changing
- YAML is better once the pipeline model stabilizes
- YAML enables external configuration, versioning, and agent discoverability

So yes: the same dict-style model can later become pipeline YAML files.

---

## 11. Clear terminology

We clarified terminology because “skill” was overloaded.

The agreed naming model is:

- **Artifacts** = typed state/resources
- **Tools** = atomic executable capabilities
- **Pipelines** = reusable workflows over tools
- **Orchestrator** = planner/executor
- **`SKILL.md`** = agent-facing invocation guide

This distinction is important.

In particular:
- internal Python execution primitives are called **Tools**
- Claude/Codex style `SKILL.md` files are the external interface layer

---

## 12. `SKILL.md` is a wrapper layer, not the core runtime

We decided that `SKILL.md` files should describe how an external coding agent should invoke a tool or pipeline.

Examples:
- `skills/ocr/SKILL.md`
- `skills/classify/SKILL.md`
- `skills/extract/SKILL.md`
- `skills/orchestrate/SKILL.md`

Each `SKILL.md` should explain:
- when to use it
- required inputs
- optional parameters
- CLI invocation examples
- expected outputs/artifacts
- restrictions/guardrails

This is separate from the Python architecture itself.

---

## 13. Artifact metadata is required for future orchestration

We decided that each artifact should carry structured metadata, likely through its `.meta.json` sidecar.

Recommended metadata fields include:
- `artifact_id`
- `artifact_type`
- `path`
- `created_at`
- `created_by_tool`
- `source_artifact_ids`
- `status`
- `params`
- `model`
- `content_hash`
- `pipeline_name`
- `run_id`

Reasons:
- reconstruct lineage
- detect staleness
- determine whether an artifact is reusable
- support orchestrator planning
- provide traceability for future agent use

---

## 14. The system should be reusable beyond the current expense workflow

A major design goal is that this should not remain an invoice-only or expense-only project.

The same framework should later support other pipelines by adding:
- new tools
- new pipelines
- new presets
- new `SKILL.md` wrappers

Examples of future expansions:
- contract OCR and clause extraction
- form digitization
- KYC / identity-document processing
- bank statement parsing
- medical document classification
- research paper ingestion
- code/documentation indexing
- media transcription or other multi-stage ETL flows with similar orchestration needs

The core framework remains the same:
- artifacts
- tools
- pipelines
- orchestrator
- agent wrappers

That is the main reason for investing in this architecture now.

---

## Target architecture

The intended architecture is:

- **Artifacts** = persistent typed outputs
- **Tools** = atomic executable units
- **Pipelines** = declarative workflows
- **Orchestrator** = dependency resolver and executor
- **Registry / Store** = filesystem-backed artifact discovery and lineage tracking
- **`SKILL.md` layer** = external machine-facing usage interface

This is the end state we are designing toward.

---

## What should be built next

Recommended implementation order:

1. add typed artifact objects
2. add `.meta.json` sidecars for all produced artifacts
3. build a filesystem-backed artifact registry
4. refactor current functionality into tool classes
5. build a thin orchestrator loop
6. define initial pipelines in Python
7. expose tool and pipeline usage through `SKILL.md`
8. later externalize pipelines to YAML

This sequence gives the shortest path to a reusable and extensible framework.

---

## Summary

We are not just building a script that OCRs invoices.

We are building a **general local-first document ETL framework** with:
- reusable artifacts
- composable tools
- declarative pipelines
- a thin orchestrator
- external `SKILL.md` wrappers for coding agents

The immediate use case is expense documents, but the design intentionally supports broader document-processing and ETL-style workflows in the future.
