from __future__ import annotations

import argparse
from pathlib import Path

from document_etl_pipeline.cli.base import BaseCliCommand
from document_etl_pipeline.engines.ocr import OcrConfig, OcrEngine


class OcrCliCommand(BaseCliCommand):
    name = "ocr"
    help = "Run OCR on JPG/JPEG images."

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
            "--output-type",
            choices=["txt", "md"],
            default="txt",
            help="OCR output format. Default: txt",
        )
        parser.add_argument(
            "--doc-hints",
            default="",
            help='Comma-separated document hints, e.g. "invoice,receipt,proof of payment"',
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

        engine = OcrEngine(
            OcrConfig(
                model=args.model,
                output_type=args.output_type,
                document_type_hints=self.parse_csv_list(args.doc_hints),
            )
        )

        failures = 0
        for image_path in image_paths:
            try:
                output_path = engine.save_transcription(image_path)
                self.print_success(f"OCR: {image_path}")
                self.print_success(f"  -> {output_path}")
            except Exception as exc:
                failures += 1
                self.print_error(f"Failed OCR {image_path}: {exc}")

        return 1 if failures else 0

    def _resolve_image_inputs(self, input_path: Path, recursive: bool) -> list[Path]:
        if input_path.is_file():
            if not OcrEngine.is_image_file(input_path):
                raise ValueError(f"Unsupported image file: {input_path}")
            return [input_path]

        return list(OcrEngine.iter_images(input_path, recursive=recursive))
