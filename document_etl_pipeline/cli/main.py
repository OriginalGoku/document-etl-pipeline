from __future__ import annotations

import argparse
from typing import Sequence

from document_etl_pipeline.cli.base import BaseCliCommand
from document_etl_pipeline.cli.classify import ClassifyCliCommand
from document_etl_pipeline.cli.convert import ConvertCliCommand
from document_etl_pipeline.cli.extract import ExtractCliCommand
from document_etl_pipeline.cli.ocr import OcrCliCommand


def build_commands() -> list[BaseCliCommand]:
    return [
        ConvertCliCommand(),
        OcrCliCommand(),
        ClassifyCliCommand(),
        ExtractCliCommand(),
    ]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="document-etl-pipeline",
        description="Document ETL pipeline CLI.",
    )

    subparsers = parser.add_subparsers(
        dest="command",
        required=True,
        help="Available commands",
    )

    for command in build_commands():
        command.add_to_subparsers(subparsers)

    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    command = getattr(args, "_command", None)
    if command is None:
        parser.print_help()
        return 1

    return command.run(args)


if __name__ == "__main__":
    raise SystemExit(main())
