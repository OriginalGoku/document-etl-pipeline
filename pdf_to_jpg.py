from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import pymupdf


@dataclass(slots=True)
class PdfConversionConfig:
    dpi: int = 300


class PdfToJpgConverter:
    def __init__(self, config: PdfConversionConfig | None = None) -> None:
        self.config = config or PdfConversionConfig()

    def convert(
        self, pdf_path: str | Path, output_dir: str | Path | None = None
    ) -> list[Path]:
        pdf_file = Path(pdf_path)
        if not pdf_file.exists():
            raise FileNotFoundError(f"PDF not found: {pdf_file}")

        if output_dir is None:
            output_path = pdf_file.with_name(f"{pdf_file.stem}_images")
        else:
            output_path = Path(output_dir)

        output_path.mkdir(parents=True, exist_ok=True)

        doc = pymupdf.open(pdf_file)
        saved_files: list[Path] = []

        try:
            zoom = self.config.dpi / 72
            matrix = pymupdf.Matrix(zoom, zoom)

            for page_no, page in enumerate(doc, start=1):
                pix = page.get_pixmap(matrix=matrix)
                jpg_file = output_path / f"{pdf_file.stem}_{page_no}.jpg"
                pix.save(str(jpg_file))
                saved_files.append(jpg_file)
        finally:
            doc.close()

        return saved_files
