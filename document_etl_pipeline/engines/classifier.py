from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import ollama

from prompts.system_prompts import ClassificationOption, SystemPrompts


@dataclass(slots=True)
class ClassifierConfig:
    model: str = "gemma4:e4b"
    options: list[ClassificationOption] = field(default_factory=list)
    ocr_output_type: str = "txt"


class DocumentClassifier:
    def __init__(self, config: ClassifierConfig | None = None) -> None:
        self.config = config or ClassifierConfig()

    def classify(self, image_path: str | Path) -> str:
        image_file = Path(image_path)
        prompt = SystemPrompts.build_classifier_prompt(self.config.options)

        ocr_path = self._find_ocr_sidecar(image_file)
        if ocr_path is not None:
            content = ocr_path.read_text(encoding="utf-8").strip()
            return self._classify_text(content=content, prompt=prompt)

        return self._classify_image(image_file=image_file, prompt=prompt)

    def save_classification(self, image_path: str | Path) -> Path:
        image_file = Path(image_path)
        classification = self.classify(image_file)
        output_path = image_file.with_name(f"{image_file.stem}.classify.txt")
        output_path.write_text(classification.strip() + "\n", encoding="utf-8")
        return output_path

    def _classify_text(self, content: str, prompt: str) -> str:
        response = ollama.chat(
            model=self.config.model,
            messages=[
                {
                    "role": "system",
                    "content": prompt,
                },
                {
                    "role": "user",
                    "content": content,
                },
            ],
            options={"temperature": 0},
        )
        return response["message"]["content"].strip()

    def _classify_image(self, image_file: Path, prompt: str) -> str:
        response = ollama.chat(
            model=self.config.model,
            messages=[
                {
                    "role": "system",
                    "content": prompt,
                },
                {
                    "role": "user",
                    "content": "Classify this document.",
                    "images": [str(image_file)],
                },
            ],
            options={"temperature": 0},
        )
        return response["message"]["content"].strip()

    def _find_ocr_sidecar(self, image_file: Path) -> Path | None:
        candidates = [
            image_file.with_name(f"{image_file.stem}.ocr.txt"),
            image_file.with_name(f"{image_file.stem}.ocr.md"),
        ]

        preferred = "md" if self.config.ocr_output_type.lower() == "md" else "txt"
        ordered = sorted(
            candidates,
            key=lambda path: 0 if path.suffix == f".{preferred}" else 1,
        )

        for candidate in ordered:
            if candidate.exists():
                return candidate

        return None