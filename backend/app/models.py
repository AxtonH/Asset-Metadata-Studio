from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class AssetTask:
    task_id: str
    source_name: str
    display_name: str
    image_path: Path


@dataclass(frozen=True)
class AssetResult:
    task_id: str
    display_name: str
    english_name: str
    arabic_name: str
    tags: str
    raw_text: str