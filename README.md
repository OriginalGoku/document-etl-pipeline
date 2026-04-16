# README

## document-etl-pipeline

Local-first document OCR, classification, extraction, and ETL pipeline.

## Overview

This project is a modular document-processing pipeline designed for engineering use cases where clear stage boundaries, reusable artifacts, and low dependency overhead matter more than product branding or marketplace discoverability.

It supports these core stages:

- PDF to JPG conversion
- OCR transcription
- Document classification
- Field extraction

Each stage can run independently or as part of a full pipeline. Outputs are written as sidecar files next to source images so intermediate artifacts remain inspectable, stable, and reusable by downstream tools or future agents.

## Design goals

- Local-first execution
- Minimal external dependencies
- Clear ETL-style pipeline stages
- Reusable intermediate artifacts
- Prompt centralization
- Model/vendor agnostic architecture
- Future compatibility with agentic tool invocation from systems like Claude Code or Codex

## Repository structure

- `app.py`  
  Main CLI entrypoint. Traverses folders and orchestrates pipeline stages.

- `pdf_to_jpg.py`  
  Converts PDFs into one JPG per page.

- `ocr_engine.py`  
  Runs OCR on JPG images and saves `.ocr.txt` or `.ocr.md` sidecar files.

- `classifier.py`  
  Classifies documents using OCR text when available, otherwise falls back to the source image.

- `field_extractor.py`  
  Extracts requested fields from OCR text when available, otherwise falls back to the source image.

- `system_prompts.py`  
  Central location for all system prompt builders and prompt-related data structures.

- `ARCHITECTURE.md`  
  Detailed architectural notes and rationale.

## Pipeline model

Typical end-to-end flow:

```text
PDF
  -> JPG pages
      -> OCR sidecar
          -> classification sidecar
          -> extraction sidecar
```

Typical partial flows:

```text
JPG -> OCR
JPG -> classification
JPG -> extraction
OCR text -> classification
OCR text -> extraction
```

The system does not require all stages to be run together.

## Sidecar outputs

For an input image:

```text
invoice_1.jpg
```

the pipeline may generate:

```text
invoice_1.ocr.txt
invoice_1.classify.txt
invoice_1.extract.txt
```

For an input PDF:

```text
invoice.pdf
```

conversion produces:

```text
invoice_images/invoice_1.jpg
invoice_images/invoice_2.jpg
...
```

## Why sidecars

Derived artifacts are stored separately instead of mutating source files, embedding metadata into OCR output, or renaming files based on model output.

Benefits:

- raw OCR remains stable
- classification can be rerun with different label sets
- extraction can be rerun with different field lists
- debugging is easier
- artifact provenance stays clear
- future agentic orchestration becomes simpler

## Installation

### Requirements

- Python 3.10+
- Ollama installed locally
- A local multimodal model available in Ollama, for example `gemma4:e4b`

### Python dependencies

```bash
python -m pip install pymupdf ollama
```

### Pull a model

```bash
ollama pull gemma4:e4b
```

## CLI usage

### Convert PDFs to JPG

```bash
python app.py "/path/to/folder" --mode convert
```

### OCR images

```bash
python app.py "/path/to/folder" --mode ocr --ocr-output-type txt --doc-hints "invoice,receipt,proof of payment"
```

### Classify documents

```bash
python app.py "/path/to/folder" --mode classify --class-options "invoice=Vendor-issued billing document;proof_of_payment=Bank statements showing flow of funds or payments made to someone;receipt=Proof of purchase issued by seller"
```

### Extract fields

```bash
python app.py "/path/to/folder" --mode extract --fields "Date,HST,Subtotal,Total,Description"
```

### Run full pipeline

```bash
python app.py "/path/to/folder" --mode all --doc-hints "invoice,receipt,proof of payment" --class-options "invoice=Vendor-issued billing document;proof_of_payment=Bank statements showing flow of funds or payments made to someone;receipt=Proof of purchase issued by seller" --fields "Date,HST,Subtotal,Total,Description"
```

## CLI options

### Shared

- `folder`  
  Root folder to scan

- `--mode`  
  One of:
  - `convert`
  - `ocr`
  - `classify`
  - `extract`
  - `all`

- `--no-recursive`  
  Scan only the top-level folder

- `--model`  
  Ollama model name. Default: `gemma4:e4b`

- `--dpi`  
  PDF render DPI. Default: `300`

### OCR

- `--ocr-output-type txt|md`
- `--doc-hints "invoice,receipt,proof of payment"`

### Classification

- `--class-options "invoice=Vendor-issued billing document;proof_of_payment=Bank statements showing flow of funds or payments made to someone;receipt=Proof of purchase issued by seller"`

Each classification option can be either:
- `label`
- `label=description`

### Extraction

- `--fields "Date,HST,Subtotal,Total,Description"`

## Prompting strategy

Prompts are intentionally minimal.

Reasons:

- smaller local models often degrade when over-constrained
- forcing strict JSON output can reduce extraction quality
- free-form OCR output is easier to inspect and reuse

Prompt construction is centralized in `system_prompts.py`.

### OCR prompt style

Examples:

- `Transcribe this document as plain text.`
- `Transcribe this document as markdown.`

With hints:

- `Transcribe this document as plain text. Use the document type hints only as guidance: invoice, receipt, proof of payment.`

### Classification prompt style

The classifier:

- receives a caller-provided label set
- may receive optional label descriptions
- returns only the selected label

### Extraction prompt style

The extractor:

- receives a caller-provided field list
- returns plain text only
- preserves labels exactly as supplied
- writes `Not found` for missing fields

## Input preference strategy

Classifier and extractor use this priority order:

1. prefer OCR sidecar text if present
2. fall back to the image if OCR is missing

This reduces repeated vision calls and makes partial reruns cheap.

## Object model

The codebase uses class-based stage encapsulation with dataclass-backed configuration objects.

Examples:

- `PdfConversionConfig`
- `OcrConfig`
- `ClassifierConfig`
- `ExtractionConfig`
- `AppConfig`
- `ClassificationOption`

This keeps stage responsibilities explicit and makes the project easier to extend into a more agentic tool framework.

## Dependency footprint

External packages are intentionally minimal:

- `pymupdf`
- `ollama`

Everything else uses the Python standard library.

## Current limitations

- OCR quality depends on the chosen local vision model
- Extraction output is still model-dependent
- There is no aggregate report builder yet
- There is no preprocessing for skewed or noisy scans
- There is no schema validation layer for extraction outputs

## Future directions

- CSV / spreadsheet export
- image preprocessing
- retry logic and confidence scoring
- multiple classifier types
- report generation
- planner / agent orchestration
- tool exposure for code agents such as Claude Code or Codex

## Naming

Recommended repository name:

```text
document-etl-pipeline
```

Recommended Python package/module namespace:

```text
document_etl_pipeline
```
