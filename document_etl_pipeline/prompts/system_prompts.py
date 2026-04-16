from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable


@dataclass(frozen=True)
class ClassificationOption:
    label: str
    description: str | None = None


class SystemPrompts:
    @staticmethod
    def build_ocr_prompt(
        output_type: str = "txt",
        document_type_hints: Iterable[str] | None = None,
    ) -> str:
        output_type = output_type.lower().strip()
        if output_type == "md":
            prompt = "Transcribe this document as markdown."
        else:
            prompt = "Transcribe this document as plain text."

        hints = [hint.strip() for hint in (document_type_hints or []) if hint.strip()]
        if hints:
            prompt += (
                f" Use the document type hints only as guidance: {', '.join(hints)}."
            )

        return prompt

    @staticmethod
    def build_classifier_prompt(
        options: Iterable[ClassificationOption],
    ) -> str:
        rendered_options: list[str] = []

        for option in options:
            label = option.label.strip()
            if not label:
                continue

            if option.description and option.description.strip():
                rendered_options.append(f"{label}: {option.description.strip()}")
            else:
                rendered_options.append(label)

        if not rendered_options:
            raise ValueError(
                "Cannot build classifier prompt without classification options."
            )

        options_text = "; ".join(rendered_options)
        return (
            f"Classify this document as one of: {options_text}. Return only the label."
        )

    @staticmethod
    def build_extraction_prompt(fields: Iterable[str]) -> str:
        clean_fields = [field.strip() for field in fields if field and field.strip()]

        if not clean_fields:
            raise ValueError(
                "Cannot build extraction prompt without fields to extract."
            )

        bullet_lines = "\n".join(f"- {field}" for field in clean_fields)
        format_lines = "\n".join(f"{field}: <value>" for field in clean_fields)

        return (
            "Read this document and extract only:\n"
            f"{bullet_lines}\n\n"
            "Rules:\n"
            "- Do not include any other fields\n"
            "- If a field is missing, write 'Not found'\n"
            "- Return plain text only\n"
            "- Preserve the values exactly as shown in the document\n\n"
            "Format:\n"
            f"{format_lines}"
        )
