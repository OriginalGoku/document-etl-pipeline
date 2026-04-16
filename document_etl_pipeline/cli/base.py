from __future__ import annotations

import argparse
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Iterable


class BaseCliCommand(ABC):
    """
    Base class for CLI subcommands.

    Concrete commands should implement:
    - name
    - help
    - register_arguments()
    - run()
    """

    name: str
    help: str

    def add_to_subparsers(
        self,
        subparsers: argparse._SubParsersAction,
    ) -> None:
        parser = subparsers.add_parser(
            self.name,
            help=self.help,
            description=self.help,
        )
        self.register_arguments(parser)
        parser.set_defaults(_command=self)

    @abstractmethod
    def register_arguments(self, parser: argparse.ArgumentParser) -> None:
        pass

    @abstractmethod
    def run(self, args: argparse.Namespace) -> int:
        pass

    @staticmethod
    def parse_csv_list(value: str | None) -> list[str]:
        if not value:
            return []
        return [item.strip() for item in value.split(",") if item.strip()]

    @staticmethod
    def ensure_input_exists(path_value: str | Path) -> Path:
        path = Path(path_value)
        if not path.exists():
            raise FileNotFoundError(f"Input not found: {path}")
        return path

    @staticmethod
    def ensure_directory(path_value: str | Path) -> Path:
        path = Path(path_value)
        if not path.exists():
            raise FileNotFoundError(f"Directory not found: {path}")
        if not path.is_dir():
            raise NotADirectoryError(f"Not a directory: {path}")
        return path

    @staticmethod
    def iter_files(
        root: Path,
        patterns: Iterable[str],
        recursive: bool = True,
    ) -> Iterable[Path]:
        iterator = root.rglob if recursive else root.glob
        seen: set[Path] = set()

        for pattern in patterns:
            for path in iterator(pattern):
                if path not in seen:
                    seen.add(path)
                    yield path

    @staticmethod
    def print_success(message: str) -> None:
        print(message)

    @staticmethod
    def print_error(message: str) -> None:
        print(message)
