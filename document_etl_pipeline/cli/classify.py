from __future__ import annotations

import argparse
from pathlib import Path

from document_etl_pipeline.cli.base import BaseCliCommand
from document_etl_pipeline.engines.classifier import (
    ClassifierConfig,
    DocumentClassifier,
)
from document_etl_pipeline.engines.ocr import OcrEngine
from document_etl_pipeline.prompts.system_prompts import ClassificationOption


class ClassifyCliCommand(BaseCliCommand):
    name = "classify"
    help = "Classify documents using OCR sidecars when available, otherwise the image."

    def register_arguments(self, parser: argparse.ArgumentParser) -> None:
        parser.add_argument(
            "--input",
            required=True,
            help="Input image file or folder.",
        )
        parser.add_argument(
            "--model",
            default="gemma4:e4b",
            help='Ollama model name. Default: "gemma4:e4b"',
        )
        parser.add_argument(
            "--class-options",
            required=True,
            help=(
                "Semicolon-separated classification options. "
                'Examples: "invoice;proof_of_payment;receipt" or '
                '"invoice=Vendor-issued billing document;'
                "proof_of_payment=Bank statements showing flow of funds;"
                'receipt=Proof of purchase issued by seller"'
            ),
        )
        parser.add_argument(
            "--ocr-output-type",
            choices=["txt", "md"],
            default="txt",
            help="Preferred OCR sidecar format. Default: txt",
        )
        parser.add_argument(
            "--recursive",
            action="store_true",
            help="Recursively scan folders.",
        )

    def run(self, args: argparse.Namespace) -> int:
        input_path = self.ensure_input_exists(args.input)
        image_paths = self._resolve_image_inputs(input_path, recursive=args.recursive)

        if not image_paths:
            self.print_success("No JPG/JPEG files found.")
            return 0

        options = self._parse_classification_options(args.class_options)

        classifier = DocumentClassifier(
            ClassifierConfig(
                model=args.model,
                options=options,
                ocr_output_type=args.ocr_output_type,
            )
        )

        failures = 0
        for image_path in image_paths:
            try:
                output_path = classifier.save_classification(image_path)
                self.print_success(f"Classified: {image_path}")
                self.print_success(f"  -> {output_path}")
            except Exception as exc:
                failures += 1
                self.print_error(f"Failed classify {image_path}: {exc}")

        return 1 if failures else 0

    def _resolve_image_inputs(self, input_path: Path, recursive: bool) -> list[Path]:
        if input_path.is_file():
            if not OcrEngine.is_image_file(input_path):
                raise ValueError(f"Unsupported image file: {input_path}")
            return [input_path]

        return list(OcrEngine.iter_images(input_path, recursive=recursive))

    def _parse_classification_options(
        self,
        class_options_value: str,
    ) -> list[ClassificationOption]:
        options: list[ClassificationOption] = []

        for raw_part in class_options_value.split(";"):
            part = raw_part.strip()
            if not part:
                continue

            if "=" in part:
                label, description = part.split("=", 1)
                label = label.strip()
                description = description.strip()
            else:
                label = part
                description = None

            if not label:
                continue

            options.append(
                ClassificationOption(
                    label=label,
                    description=description or None,
                )
            )

        if not options:
            raise ValueError("At least one valid classification option is required.")

        return options
