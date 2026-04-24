# README

## document-etl-pipeline

Local-first document OCR, classification, extraction, and ETL pipeline.

## Overview

This project is a modular document-processing pipeline designed for engineering use cases where clear stage boundaries, reusable artifacts, and low dependency overhead matter more than branding or marketplace discoverability.

It currently supports these core capabilities:

- convert PDF files into JPG page images
- run OCR on JPG/JPEG images
- classify documents using a configurable set of labels
- extract caller-defined fields from documents

Each capability is exposed as its own CLI command. Outputs are written as sidecar files next to source images so intermediate artifacts remain inspectable and reusable.

## Current package structure

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

## Design goals

- local-first execution
- minimal dependencies
- small, composable tools
- sidecar-based outputs
- model/vendor agnostic architecture
- clean CLI contracts for use from coding agents
- future expansion into more advanced pipelines

## Core concepts

### Engines
Execution logic lives in `engines/`.

Current engines:
- `ocr.py`
- `classifier.py`
- `extractor.py`
- `converter.py`

These are the Python implementation layer.

### CLI
CLI commands live in `cli/`.

Current commands:
- `convert`
- `ocr`
- `classify`
- `extract`

Each command is implemented as a class inheriting from a shared base command in `cli/base.py`.

### Prompts
Prompt builders and prompt-related data structures live in:

- `prompts/system_prompts.py`

This keeps prompt logic centralized and out of the engine implementations.

### Sidecar outputs
For an input image like:

```text
invoice_1.jpg
```

the pipeline may generate:

```text
invoice_1.ocr.txt
invoice_1.classify.txt
invoice_1.extract.txt
```

For an input PDF like:

```text
invoice.pdf
```

conversion generates:

```text
invoice_images/invoice_1.jpg
invoice_images/invoice_2.jpg
...
```

## Why sidecars

Derived artifacts are stored next to their source artifacts instead of:
- mutating source files
- embedding metadata into OCR files
- renaming files based on model output

Benefits:
- raw OCR stays stable
- extraction can be rerun with different fields
- classification can be rerun with different labels
- debugging is easier
- downstream tools can reuse outputs

## Installation

### Requirements

- Python 3.10+
- Ollama installed locally
- a local multimodal model available in Ollama, for example `gemma4:e4b`

### Python dependencies

```bash
python -m pip install pymupdf ollama
```

### Pull a model

```bash
ollama pull gemma4:e4b
```

## Running the CLI

You can run the package as a module:

```bash
python -m document_etl_pipeline --help
```

### Convert PDFs to JPG

```bash
python -m document_etl_pipeline convert --input "/path/to/folder" --recursive --dpi 300
```

### OCR images

```bash
python -m document_etl_pipeline ocr --input "/path/to/folder" --recursive --output-type txt --doc-hints "invoice,receipt,proof of payment"
```

### Classify documents

```bash
python -m document_etl_pipeline classify --input "/path/to/folder" --recursive --class-options "invoice;proof_of_payment=Bank statements showing flow of funds or payments made to someone;receipt=Proof of purchase issued by seller"
```

### Extract fields

```bash
python -m document_etl_pipeline extract --input "/path/to/folder" --recursive --fields "Date,HST,Subtotal,Total,Description"
```

## CLI commands

### `convert`
Converts PDFs into JPG page images.

#### Input
- one PDF file, or
- one folder containing PDFs

#### Main options
- `--input`
- `--recursive`
- `--dpi`

#### Output
- JPG page images in a `*_images` folder next to the PDF

### `ocr`
Runs OCR on JPG/JPEG images.

#### Input
- one image file, or
- one folder containing images

#### Main options
- `--input`
- `--recursive`
- `--model`
- `--output-type txt|md`
- `--doc-hints`

#### Output
- `name.ocr.txt` or `name.ocr.md`

### `classify`
Classifies documents using OCR sidecars when available, otherwise falls back to the image.

#### Input
- one image file, or
- one folder containing images

#### Main options
- `--input`
- `--recursive`
- `--model`
- `--classes`
- `--class-descriptions`
- `--ocr-output-type`

#### Output
- `name.classify.txt`

### `extract`
Extracts caller-defined fields using OCR sidecars when available, otherwise falls back to the image.

#### Input
- one image file, or
- one folder containing images

#### Main options
- `--input`
- `--recursive`
- `--model`
- `--fields`
- `--ocr-output-type`

#### Output
- `name.extract.txt`

## Prompting strategy

Prompts are intentionally minimal.

Reasons:
- smaller local models often degrade when over-constrained
- forcing strict JSON output can reduce quality
- plain text output is easier to inspect and reuse

Prompt construction is centralized in `prompts/system_prompts.py`.

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

## Current design direction

The current implementation is intentionally simple:
- engines do the work
- CLI commands expose each tool clearly
- coding agents can orchestrate those commands externally

This keeps the product lightweight while still being useful.

A future version may add:
- artifact metadata sidecars
- reusable pipelines
- an internal orchestrator
- YAML-defined workflows

## Intended use with coding agents

This repository is being shaped so systems like Claude Code or Codex can invoke it through:
- atomic CLI commands
- clear side effects
- predictable sidecar outputs
- `SKILL.md` wrappers

The short-term plan is:
- keep the Python tools simple
- let the external coding agent act as the orchestrator

## Dependency footprint

External packages are intentionally minimal:

- `pymupdf`
- `ollama`

Everything else uses the Python standard library.

## Current limitations

- OCR quality depends on the chosen local model
- extraction output is still model-dependent
- there is no built-in orchestration layer yet
- there is no artifact metadata layer yet
- there is no formal pipeline registry yet
- there is no aggregate report builder yet

## Future directions

- artifact metadata sidecars
- reusable pipeline definitions
- internal orchestrator
- YAML pipeline configs
- CSV / spreadsheet export
- image preprocessing
- richer `SKILL.md` wrappers
- additional document-processing pipelines beyond expenses

## Naming

Recommended repository name:

```text
document-etl-pipeline
```

Recommended Python package namespace:

```text
document_etl_pipeline
```
