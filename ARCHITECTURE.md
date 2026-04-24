# ARCHITECTURE

## document-etl-pipeline

## 1. Current architectural direction

This project is currently positioned as a **simple, tool-first document ETL product**, not a full internal orchestration framework.

The immediate goal is practical usefulness:

- expose a small set of clear document-processing tools
- make each tool callable from a stable CLI
- make outputs predictable and reusable
- allow external coding agents such as Claude Code or Codex to orchestrate those tools

That means the architecture is intentionally biased toward:
- simplicity
- explicit interfaces
- low dependency overhead
- clean side effects
- future extensibility without building too much too early

---

## 2. Current system shape

The current design is based on four layers:

- **Engines**
- **CLI**
- **Prompts**
- **Sidecar outputs**

This is the intentionally simplified version of the broader long-term design.

### Current package structure

```text
document_etl_pipeline/
  __init__.py
  __main__.py
  cli/
    __init__.py
    base.py
    main.py
    ocr.py
    classify.py
    extract.py
    convert.py
  engines/
    __init__.py
    ocr.py
    classifier.py
    extractor.py
    converter.py
  prompts/
    __init__.py
    system_prompts.py
```

---

## 3. Layer responsibilities

## 3.1 Engines

The `engines/` package contains the execution logic.

Current engines:
- `ocr.py`
- `classifier.py`
- `extractor.py`
- `converter.py`

These modules contain the actual implementation of the document-processing capabilities.

### Engine responsibilities
Each engine should:
- encapsulate one major capability
- expose a clear Python API
- avoid CLI parsing concerns
- avoid orchestration concerns
- avoid scattered prompt construction

### Current engine roles

#### `converter.py`
Converts PDFs into JPG page images.

Current core class:
- `PdfToJpgConverter`

Related config:
- `PdfConversionConfig`

#### `ocr.py`
Runs OCR on JPG/JPEG images.

Current core class:
- `OcrEngine`

Related config:
- `OcrConfig`

#### `classifier.py`
Classifies documents based on OCR text when available, otherwise the image.

Current core class:
- `DocumentClassifier`

Related config:
- `ClassifierConfig`

#### `extractor.py`
Extracts caller-defined fields from OCR text when available, otherwise the image.

Current core class:
- `FieldExtractor`

Related config:
- `ExtractionConfig`

---

## 3.2 CLI

The `cli/` package is the command-line interface layer.

This is the public operational interface for:
- humans
- automation scripts
- coding agents
- future `SKILL.md` wrappers

### Design approach
The CLI is intentionally implemented in a modular, class-based way.

There is:
- a shared base command in `cli/base.py`
- one concrete command class per tool
- a central dispatcher in `cli/main.py`

### Current command set
- `convert`
- `ocr`
- `classify`
- `extract`

### Why this design was chosen
- avoids one oversized `--mode` switch
- gives each tool a clean input/output contract
- simplifies help text and discoverability
- makes `SKILL.md` examples straightforward
- allows coding agents to invoke only the tool they need

### `BaseCliCommand`
The base CLI class exists to centralize:
- argument registration pattern
- input validation helpers
- CSV parsing helpers
- file iteration helpers
- output/error reporting conventions

This avoids duplicated CLI boilerplate while keeping subclass logic small.

### Concrete CLI commands
Each concrete command:
- defines its name
- defines its help text
- registers its specific arguments
- instantiates the appropriate engine/config
- resolves file/folder traversal
- executes its per-file loop

The goal is modularity without overengineering.

---

## 3.3 Prompts

Prompt builders are centralized in:

- `prompts/system_prompts.py`

### Why prompt centralization matters
- prompt logic should not be duplicated across engines
- prompt experimentation should be isolated
- model-facing instructions should be easy to audit
- business logic should stay cleaner

### Current prompt builder responsibilities
- OCR prompt generation
- classifier prompt generation
- extractor prompt generation

### Prompting philosophy
The prompting strategy is deliberately minimal.

Reasons:
- smaller local models degrade under overly rigid prompting
- forcing JSON output reduced output quality in practice
- plain text and markdown outputs are easier to inspect and reuse

This is a deliberate product-driven decision, not an omission.

---

## 4. Sidecar output architecture

The current system uses **sidecar outputs** rather than in-place mutation.

For an image like:

```text
invoice_1.jpg
```

the system may generate:

```text
invoice_1.ocr.txt
invoice_1.classify.txt
invoice_1.extract.txt
```

For a PDF like:

```text
invoice.pdf
```

conversion produces:

```text
invoice_images/invoice_1.jpg
invoice_images/invoice_2.jpg
...
```

### Why sidecars were chosen
Instead of:
- rewriting source files
- embedding metadata into OCR files
- renaming files based on model decisions

the system writes outputs beside the original artifact.

### Benefits
- raw outputs remain inspectable
- OCR can be reused by classifier/extractor
- classification can be rerun with different labels
- extraction can be rerun with different fields
- downstream tools can consume stable files
- coding agents can reason about file effects more easily

This is one of the key architectural choices.

---

## 5. OCR-first reuse model

A major design decision is that downstream operations should prefer OCR sidecars when available.

### Current priority order
For classification and extraction:
1. prefer OCR sidecar text
2. fall back to the original image if OCR is missing

### Why
- avoids repeated vision inference
- keeps costs lower
- improves modularity
- creates a stable intermediate representation
- supports partial reruns

This is effectively the first step toward a fuller artifact model, even though a formal artifact registry does not exist yet.

---

## 6. Why there is no internal orchestrator yet

A major decision was made to **not** build the full orchestration framework immediately.

### Reason
For a quick, useful product, the simpler path is:

- build reliable tools
- expose them as clear CLI commands
- let Claude Code / Codex orchestrate them externally

### What this means
Right now:
- the repo provides capabilities
- the external coding agent provides orchestration

This is a deliberate product choice.

### Benefits
- faster shipping
- less internal complexity
- easier iteration
- simpler mental model
- avoids premature architecture work

### What is deferred
- internal dependency resolution
- artifact lineage tracking
- stale artifact detection
- declarative pipeline execution
- internal planner/executor loop

These remain future options, not current requirements.

---

## 7. Coding-agent-first interface design

Because the intended users include coding agents, the architecture is optimized for:

- explicit subcommands
- predictable output files
- low ambiguity
- minimal hidden behavior

### Why this matters
A coding agent works better when it can rely on:
- simple command contracts
- direct file effects
- stable naming conventions
- concise documentation in `SKILL.md`

This is why the CLI matters so much in the current version.

---

## 8. Relationship between engines, CLI, and `SKILL.md`

It is important to keep these separate.

### Engines
- internal Python execution logic

### CLI
- executable interface over the engines

### `SKILL.md`
- agent-facing documentation layer explaining when and how to call the CLI

This separation prevents confusion around the word “skill.”

In this architecture:
- OCR/classify/extract/convert are **tools exposed through CLI**
- `SKILL.md` files are wrappers that tell a coding agent how to use them

---

## 9. Current command architecture

## 9.1 Top-level command dispatch

The package can be invoked through:

```bash
python -m document_etl_pipeline ...
```

The top-level dispatcher in `cli/main.py`:
- builds the root parser
- registers subcommands
- dispatches execution to the selected command object

## 9.2 Subcommand model

Each tool has a dedicated command.

Examples:
- `python -m document_etl_pipeline convert ...`
- `python -m document_etl_pipeline ocr ...`
- `python -m document_etl_pipeline classify ...`
- `python -m document_etl_pipeline extract ...`

This is cleaner than a single command with a giant argument surface.

---

## 10. Object-oriented design choices

The codebase uses OOP selectively and pragmatically.

### Why OOP is used here
- engines have stable responsibilities
- CLI commands benefit from a common base class
- config objects are easier to express with dataclasses
- future expansion remains manageable

### Why dataclasses are used
Dataclasses are used for:
- engine configuration
- structured prompt options
- cleaner default handling
- readability

Examples:
- `OcrConfig`
- `ClassifierConfig`
- `ExtractionConfig`
- `PdfConversionConfig`
- `ClassificationOption`

This is enough structure without creating a heavy framework.

---

## 11. What we are intentionally not building yet

The following ideas were discussed, but intentionally deferred:

- formal artifact registry
- `.meta.json` artifact sidecars
- internal orchestrator
- declarative pipelines
- YAML pipeline definitions
- staleness checks
- full dependency graph resolution

### Why these are deferred
They make sense architecturally, but they are not required to ship a useful product now.

The current bias is:
- ship useful tools first
- use external coding agents as orchestrators
- internalize orchestration only when real pain appears

---

## 12. Future architectural expansion path

The current design leaves room to evolve into a richer system later.

### Likely next evolution
- add artifact metadata sidecars
- add a lightweight artifact model
- introduce pipelines as reusable workflow definitions
- add an internal orchestrator
- externalize pipelines into YAML

### Important point
The current engines and CLI layout do not block that future.

That is why the current structure is still a good foundation even though it is intentionally simpler.

---

## 13. Reusability beyond expense documents

The current use case is expense processing, but the architecture is deliberately broader.

The same approach can later support:
- contract OCR and clause extraction
- form digitization
- KYC / identity documents
- bank statement processing
- healthcare documents
- research paper ingestion
- other multi-stage ETL/document workflows

The reusable parts are:
- engine layer
- CLI layer
- prompt layer
- sidecar convention
- future `SKILL.md` wrappers

This is why the repository name remains broad and engineering-oriented.

---

## 14. Summary

The current architecture is a **tool-first document ETL product** with:

- modular engines
- clean CLI subcommands
- centralized prompt builders
- predictable sidecar outputs
- external coding-agent orchestration

This is intentionally simpler than the full long-term framework vision.

That simplicity is a feature:
- it ships faster
- it is easier to reason about
- it is easier for Claude Code / Codex to use
- it keeps the door open for future pipelines and orchestration if they become necessary
