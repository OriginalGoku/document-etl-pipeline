from __future__ import annotations

import argparse
from dataclasses import dataclass, field
from pathlib import Path

from field_extractor import ExtractionConfig, FieldExtractor

from classifier import ClassifierConfig, DocumentClassifier
from ocr_engine import OcrConfig, OcrEngine
from pdf_to_jpg import PdfConversionConfig, PdfToJpgConverter
from system_prompts import ClassificationOption


@dataclass(slots=True)
class AppConfig:
    folder: Path
    mode: str = "all"
    recursive: bool = True
    dpi: int = 300
    model: str = "gemma4:e4b"
    ocr_output_type: str = "txt"
    document_type_hints: list[str] = field(default_factory=list)
    classes: list[ClassificationOption] = field(default_factory=list)
    fields: list[str] = field(default_factory=list)


class DocumentProcessingApp:
    def __init__(self, config: AppConfig) -> None:
        self.config = config

        self.pdf_converter = PdfToJpgConverter(PdfConversionConfig(dpi=config.dpi))
        self.ocr_engine = OcrEngine(
            OcrConfig(
                model=config.model,
                output_type=config.ocr_output_type,
                document_type_hints=config.document_type_hints,
            )
        )
        self.classifier = DocumentClassifier(
            ClassifierConfig(
                model=config.model,
                options=config.classes,
                ocr_output_type=config.ocr_output_type,
            )
        )
        self.extractor = FieldExtractor(
            ExtractionConfig(
                model=config.model,
                fields=config.fields,
                ocr_output_type=config.ocr_output_type,
            )
        )

    def run(self) -> None:
        if self.config.mode == "convert":
            self.run_convert()
        elif self.config.mode == "ocr":
            self.run_ocr()
        elif self.config.mode == "classify":
            self.run_classify()
        elif self.config.mode == "extract":
            self.run_extract()
        elif self.config.mode == "all":
            self.run_convert()
            self.run_ocr()
            self.run_classify()
            self.run_extract()
        else:
            raise ValueError(f"Unsupported mode: {self.config.mode}")

    def run_convert(self) -> None:
        found_any = False
        for pdf_file in self.iter_pdfs():
            found_any = True
            try:
                saved = self.pdf_converter.convert(pdf_file)
                print(f"Converted: {pdf_file}")
                for item in saved:
                    print(f"  -> {item}")
            except Exception as exc:
                print(f"Failed converting {pdf_file}: {exc}")

        if not found_any:
            print("No PDF files found.")

    def run_ocr(self) -> None:
        found_any = False
        for image_path in self.iter_images():
            found_any = True
            try:
                output_path = self.ocr_engine.save_transcription(image_path)
                print(f"OCR: {image_path}")
                print(f"  -> {output_path}")
            except Exception as exc:
                print(f"Failed OCR {image_path}: {exc}")

        if not found_any:
            print("No JPG/JPEG files found.")

    def run_classify(self) -> None:
        if not self.config.classes:
            print("No classifications provided. Skipping classify mode.")
            return

        found_any = False
        for image_path in self.iter_images():
            found_any = True
            try:
                output_path = self.classifier.save_classification(image_path)
                print(f"Classified: {image_path}")
                print(f"  -> {output_path}")
            except Exception as exc:
                print(f"Failed classify {image_path}: {exc}")

        if not found_any:
            print("No JPG/JPEG files found.")

    def run_extract(self) -> None:
        if not self.config.fields:
            print("No fields provided. Skipping extract mode.")
            return

        found_any = False
        for image_path in self.iter_images():
            found_any = True
            try:
                output_path = self.extractor.save_extraction(image_path)
                print(f"Extracted: {image_path}")
                print(f"  -> {output_path}")
            except Exception as exc:
                print(f"Failed extract {image_path}: {exc}")

        if not found_any:
            print("No JPG/JPEG files found.")

    def iter_pdfs(self):
        iterator = (
            self.config.folder.rglob
            if self.config.recursive
            else self.config.folder.glob
        )
        yield from iterator("*.pdf")

    def iter_images(self):
        yield from self.ocr_engine.iter_images(
            self.config.folder,
            recursive=self.config.recursive,
        )


def parse_csv_list(value: str | None) -> list[str]:
    if not value:
        return []
    return [item.strip() for item in value.split(",") if item.strip()]


def parse_classification_options(
    classes_value: str | None,
    descriptions_value: str | None,
) -> list[ClassificationOption]:
    labels = parse_csv_list(classes_value)
    descriptions_map: dict[str, str] = {}

    if descriptions_value:
        for raw_part in descriptions_value.split(";"):
            part = raw_part.strip()
            if not part or "=" not in part:
                continue
            key, value = part.split("=", 1)
            key = key.strip()
            value = value.strip()
            if key and value:
                descriptions_map[key] = value

    return [
        ClassificationOption(label=label, description=descriptions_map.get(label))
        for label in labels
    ]


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Convert PDFs to JPG, OCR images, classify documents, extract fields, or run all."
    )
    parser.add_argument("folder", type=str, help="Root folder to scan.")
    parser.add_argument(
        "--mode",
        choices=["convert", "ocr", "classify", "extract", "all"],
        default="all",
        help="Processing mode. Default: all",
    )
    parser.add_argument(
        "--dpi",
        type=int,
        default=300,
        help="PDF render DPI. Default: 300",
    )
    parser.add_argument(
        "--model",
        type=str,
        default="gemma4:e4b",
        help='Ollama model name. Default: "gemma4:e4b"',
    )
    parser.add_argument(
        "--ocr-output-type",
        choices=["txt", "md"],
        default="txt",
        help="OCR sidecar format. Default: txt",
    )
    parser.add_argument(
        "--doc-hints",
        type=str,
        default="",
        help='Comma-separated OCR hint list, e.g. "invoice,receipt,proof of payment"',
    )
    parser.add_argument(
        "--classes",
        type=str,
        default="",
        help='Comma-separated class labels, e.g. "invoice,proof_of_payment,receipt"',
    )
    parser.add_argument(
        "--class-descriptions",
        type=str,
        default="",
        help=(
            "Semicolon-separated label descriptions, "
            'e.g. "invoice=Vendor billing document;proof_of_payment=Bank statements showing flow of funds"'
        ),
    )
    parser.add_argument(
        "--fields",
        type=str,
        default="",
        help='Comma-separated fields to extract, e.g. "Date,HST,Subtotal,Total,Description"',
    )
    parser.add_argument(
        "--no-recursive",
        action="store_true",
        help="Only scan the top-level folder.",
    )
    return parser


def main() -> None:
    parser = build_arg_parser()
    args = parser.parse_args()

    folder = Path(args.folder)
    if not folder.exists():
        raise FileNotFoundError(f"Folder not found: {folder}")
    if not folder.is_dir():
        raise NotADirectoryError(f"Not a directory: {folder}")

    config = AppConfig(
        folder=folder,
        mode=args.mode,
        recursive=not args.no_recursive,
        dpi=args.dpi,
        model=args.model,
        ocr_output_type=args.ocr_output_type,
        document_type_hints=parse_csv_list(args.doc_hints),
        classes=parse_classification_options(args.classes, args.class_descriptions),
        fields=parse_csv_list(args.fields),
    )

    app = DocumentProcessingApp(config)
    app.run()


if __name__ == "__main__":
    main()

# Convert PDF to JPG only
# python app.py "/Users/god/Backup from Old Laptop/CEU Property/Expenses/2025/Jan 2025" --mode convert
#
# ORC Only
# python app.py "/Users/god/Backup from Old Laptop/CEU Property/Expenses/2025/Jan 2025" --mode ocr
#
# Both
# python app.py "/Users/god/Backup from Old Laptop/CEU Property/Expenses/2025/Jan 2025" --mode both
