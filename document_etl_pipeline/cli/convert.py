from __future__ import annotations

import argparse
from pathlib import Path

from document_etl_pipeline.cli.base import BaseCliCommand
from document_etl_pipeline.engines.converter import (
    PdfConversionConfig,
    PdfToJpgConverter,
)


class ConvertCliCommand(BaseCliCommand):
    name = "convert"
    help = "Convert PDF files into JPG page images."

    def register_arguments(self, parser: argparse.ArgumentParser) -> None:
        parser.add_argument(
            "--input",
            required=True,
            help="Input PDF file or folder.",
        )
        parser.add_argument(
            "--dpi",
            type=int,
            default=300,
            help="PDF render DPI. Default: 300",
        )
        parser.add_argument(
            "--recursive",
            action="store_true",
            help="Recursively scan folders.",
        )

    def run(self, args: argparse.Namespace) -> int:
        input_path = self.ensure_input_exists(args.input)
        pdf_paths = self._resolve_pdf_inputs(input_path, recursive=args.recursive)

        if not pdf_paths:
            self.print_success("No PDF files found.")
            return 0

        converter = PdfToJpgConverter(PdfConversionConfig(dpi=args.dpi))

        failures = 0
        for pdf_path in pdf_paths:
            try:
                output_files = converter.convert(pdf_path)
                self.print_success(f"Converted: {pdf_path}")
                for output_file in output_files:
                    self.print_success(f"  -> {output_file}")
            except Exception as exc:
                failures += 1
                self.print_error(f"Failed converting {pdf_path}: {exc}")

        return 1 if failures else 0

    def _resolve_pdf_inputs(self, input_path: Path, recursive: bool) -> list[Path]:
        if input_path.is_file():
            if input_path.suffix.lower() != ".pdf":
                raise ValueError(f"Unsupported PDF file: {input_path}")
            return [input_path]

        return list(
            self.iter_files(input_path, patterns=["*.pdf"], recursive=recursive)
        )
