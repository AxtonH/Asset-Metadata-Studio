from __future__ import annotations

from pathlib import Path
from typing import Iterable

from openpyxl import Workbook

from .models import AssetResult


HEADERS = [
    "Uploaded file name",
    "Asset name (English)",
    "Asset name (Arabic)",
    "Tags",
]


def write_excel(results: Iterable[AssetResult], output_path: Path) -> None:
    workbook = Workbook()
    sheet = workbook.active
    sheet.title = "Assets"

    sheet.append(HEADERS)
    for result in results:
        sheet.append(
            [
                result.display_name,
                result.english_name,
                result.arabic_name,
                result.tags,
            ]
        )

    workbook.save(output_path)
