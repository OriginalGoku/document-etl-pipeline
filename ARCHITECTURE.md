# ARCHITECTURE

## 1. Architectural goals

This project is designed around a few explicit principles:

- Local-first execution
- Minimal dependencies
- Modular stages with stable interfaces
- Inspectable intermediate artifacts
- Reusability for future agentic orchestration
- Reduced prompt rigidity to improve small-model performance

The result is a staged pipeline in which each processing step can be run independently and can consume either source images or prior stage outputs.

## 2. High-level system design

The system is built around five main modules:

- `pdf_to_jpg.py`
- `ocr_engine.py`
- `classifier.py`
- `field_extractor.py`
- `app.py`

Prompt construction is centralized in:

- `system_prompts.py`

The orchestration model is intentionally simple:

- `app.py` scans the filesystem
- it delegates work to stage-specific classes
- each stage writes its own sidecar output
- later stages prefer existing sidecar files over reprocessing images

## 3. Data flow

### Full pipeline

```text
PDF
  -> JPG pages
      -> OCR sidecar
          -> classification sidecar
          -> extraction sidecar
```

### Partial pipeline examples

```text
JPG -> OCR
JPG -> classification
JPG -> extraction
OCR text -> classification
OCR text -> extraction
```

The system does not require the full pipeline to run in a fixed sequence. That is a deliberate design choice.

## 4. Module responsibilities

### 4.1 `pdf_to_jpg.py`

Primary responsibility:

- Convert a PDF into one JPG per page

Key design points:

- Uses `PyMuPDF` via `pymupdf`
- Encapsulated in `PdfToJpgConverter`
- Configuration stored in `PdfConversionConfig`
- Default DPI is `300`
- Output naming follows page-based convention:
  - `file_images/file_1.jpg`
  - `file_images/file_2.jpg`

This module is intentionally narrow and does not know anything about OCR, classification, or extraction.

### 4.2 `ocr_engine.py`

Primary responsibility:

- Generate a text transcription from a JPG image

Key design points:

- Encapsulated in `OcrEngine`
- Configuration stored in `OcrConfig`
- Supports `txt` and `md` output
- Supports optional document type hints
- Saves sidecar files:
  - `name.ocr.txt`
  - `name.ocr.md`

Important architectural decision:

- OCR output is treated as a reusable intermediate representation
- OCR files are not modified by later stages

### 4.3 `classifier.py`

Primary responsibility:

- Assign a document class label from a caller-provided set

Key design points:

- Encapsulated in `DocumentClassifier`
- Configuration stored in `ClassifierConfig`
- Labels are represented with `ClassificationOption`
- Each class may include an optional description
- Saves sidecar files:
  - `name.classify.txt`

Behavior:

- Prefer OCR sidecar input
- Fall back to image input if OCR sidecar is missing
- Output only the selected class label

Why descriptions exist:

- They help disambiguate classes without forcing long prompts
- Example:
  - `proof_of_payment=Bank statements showing flow of funds or payments made to someone`

### 4.4 `field_extractor.py`

Primary responsibility:

- Extract only selected fields from a document

Key design points:

- Encapsulated in `FieldExtractor`
- Configuration stored in `ExtractionConfig`
- Saves sidecar files:
  - `name.extract.txt`

Behavior:

- Prefer OCR sidecar input
- Fall back to image input if OCR sidecar is missing
- Output remains plain text, not JSON

Important design decision:

- Field labels are preserved exactly as provided by the caller
- This keeps extraction generic and caller-controlled

### 4.5 `system_prompts.py`

Primary responsibility:

- Centralize all prompt construction

Key design points:

- `SystemPrompts` contains static builder methods
- `ClassificationOption` is a prompt-related data structure

Why centralize prompts:

- Keeps business logic free of prompt strings
- Makes prompt iteration safer
- Simplifies future experimentation with model behavior
- Reduces duplication across modules

### 4.6 `app.py`

Primary responsibility:

- Traverse directories
- Parse CLI arguments
- Instantiate configured components
- Orchestrate stage execution

Key design points:

- `AppConfig` holds runtime configuration
- `DocumentProcessingApp` provides stage-level methods:
  - `run_convert`
  - `run_ocr`
  - `run_classify`
  - `run_extract`
  - `run`

Supported modes:

- `convert`
- `ocr`
- `classify`
- `extract`
- `all`

## 5. Object-oriented design

The project uses OOP selectively, not excessively.

### Why OOP here

- Each stage has a stable responsibility
- Each stage benefits from explicit configuration
- Later expansion to tool/agent orchestration is easier when stages are class-based
- Unit testing is cleaner when behavior is encapsulated

### Why dataclasses are used

Dataclasses are used for configuration and simple structured inputs because they provide:

- concise declarations
- strong readability
- explicit defaults
- clean separation between runtime behavior and configuration state

Examples:

- `PdfConversionConfig`
- `OcrConfig`
- `ClassifierConfig`
- `ExtractionConfig`
- `AppConfig`
- `ClassificationOption`

## 6. Sidecar file architecture

A major design decision in this project is the use of sidecar files.

### Sidecar outputs

For an input `invoice_1.jpg`, the system may create:

- `invoice_1.ocr.txt`
- `invoice_1.classify.txt`
- `invoice_1.extract.txt`

### Why sidecars were chosen

Instead of:

- embedding metadata into OCR files
- renaming files based on classification
- storing everything in one monolithic output file

the system writes each derived artifact separately.

Benefits:

- raw OCR stays stable
- outputs are independently reproducible
- different extraction strategies can coexist
- different classifiers can coexist
- debugging is easier
- future agents can reason over explicit artifacts

This matters because classification may change depending on:

- the label set
- the prompt wording
- the model
- the business use case

Renaming the source or mutating OCR output would make that brittle.

## 7. Prompt architecture

Prompting is minimal by design.

### Reasoning

Small local models often degrade when forced into:

- strict JSON output
- long instruction lists
- excessive schema constraints

So this system uses lightweight prompt builders.

### OCR prompting

Examples:

- `Transcribe this document as plain text.`
- `Transcribe this document as markdown.`
- With hints:
  - `Use the document type hints only as guidance: invoice, receipt, proof of payment.`

### Classification prompting

The classifier prompt:

- provides labels
- optionally provides label descriptions
- requires returning only the label

This keeps the output simple and machine-consumable without requiring JSON.

### Extraction prompting

The extractor prompt:

- lists exactly the requested fields
- forbids extra fields
- asks for plain text
- asks for exact preservation of visible values
- instructs missing values to be returned as `Not found`

This mirrors the user's preferred extraction style.

## 8. Input preference strategy

Classifier and extractor both implement the same priority order:

1. Prefer OCR sidecar text if present
2. Fall back to the image if OCR is missing

This design has practical benefits:

- OCR can be reused across multiple downstream tasks
- repeated model vision calls are reduced
- later tasks can run even if only some artifacts exist
- partial reruns are cheap and simple

## 9. Dependency strategy

Dependencies are intentionally minimal.

### External packages

- `pymupdf`
- `ollama`

### Standard library use

Everything else is built with the standard library:

- `argparse`
- `dataclasses`
- `pathlib`
- `typing`

This improves portability and reduces install friction.

## 10. Error handling philosophy

The current code follows a simple error-handling approach:

- per-file errors do not stop the full traversal
- failures are printed and processing continues
- each module raises normal Python exceptions internally
- orchestration catches exceptions at the file-processing level

This is sufficient for batch processing and keeps the implementation straightforward.

## 11. Extensibility path

The architecture is intentionally aligned with future agentic expansion.

### Why it is agent-friendly

Each stage has:

- a clear input contract
- a clear output contract
- isolated side effects
- stable sidecar artifacts

This means a future planner/agent could decide:

- run OCR first
- inspect OCR output
- run classifier with one label set
- run extraction only for invoices
- run a second classifier for expense category
- generate a final aggregate report

without changing the core stage implementations.

### Likely future modules

- `expense_categorizer.py`
- `report_builder.py`
- `csv_exporter.py`
- `image_preprocessor.py`
- `document_router.py`
- `agent.py`

## 12. Tradeoffs

### Chosen tradeoffs

- Plain text over JSON for model outputs
- Sidecar files over in-place mutation
- Simplicity over heavy workflow tooling
- OOP with dataclasses over functional-only scripting
- Reusable stages over a single monolithic script

### Costs of these choices

- More files per source image
- No strict machine-validated schema
- Need for downstream parsing if aggregate reporting is later added
- Some repeated model calls if stages are run separately without OCR reuse

These are acceptable tradeoffs for the current goal: local, modular, inspectable processing.

## 13. Summary

The architecture is a modular document-processing pipeline built for local model usage and future extensibility.

Its defining characteristics are:

- sidecar-based outputs
- minimal prompts
- OCR-first reusable intermediates
- configurable classification and extraction
- low dependency footprint
- stage isolation suitable for future agent orchestration
