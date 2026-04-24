from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable

import ollama

from document_etl_pipeline.prompts import SystemPrompts


@dataclass(slots=True)
class OcrConfig:
    model: str = "gemma4:e4b"
    output_type: str = "txt"
    document_type_hints: list[str] = field(default_factory=list)


class OcrEngine:
    def __init__(self, config: OcrConfig | None = None) -> None:
        self.config = config or OcrConfig()

    def transcribe_image(self, image_path: str | Path) -> str:
        image_file = Path(image_path)
        if not image_file.exists():
            raise FileNotFoundError(f"Image not found: {image_file}")

        prompt = SystemPrompts.build_ocr_prompt(
            output_type=self.config.output_type,
            document_type_hints=self.config.document_type_hints,
        )

        response = ollama.chat(
            model=self.config.model,
            messages=[
                {
                    "role": "system",
                    "content": prompt,
                },
                {
                    "role": "user",
                    "content": "Transcribe this document.",
                    "images": [str(image_file)],
                },
            ],
            options={"temperature": 0},
        )

        return response["message"]["content"].strip()

    def save_transcription(self, image_path: str | Path) -> Path:
        image_file = Path(image_path)
        content = self.transcribe_image(image_file)
        output_path = self._get_output_path(image_file)
        output_path.write_text(content, encoding="utf-8")
        return output_path

    def _get_output_path(self, image_path: Path) -> Path:
        ext = "md" if self.config.output_type.lower() == "md" else "txt"
        return image_path.with_name(f"{image_path.stem}.ocr.{ext}")

    @staticmethod
    def is_image_file(path: Path) -> bool:
        return path.suffix.lower() in {".jpg", ".jpeg"}

    @staticmethod
    def iter_images(folder: Path, recursive: bool = True) -> Iterable[Path]:
        iterator = folder.rglob if recursive else folder.glob
        seen: set[Path] = set()

        for pattern in ("*.jpg", "*.jpeg", "*.JPG", "*.JPEG"):
            for path in iterator(pattern):
                if path not in seen:
                    seen.add(path)
                    yield path
