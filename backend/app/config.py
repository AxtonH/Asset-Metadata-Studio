from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parents[2]
BACKEND_DIR = BASE_DIR / "backend"
DATA_DIR = BACKEND_DIR / "data"
STATIC_DIR = BACKEND_DIR / "static"

DEFAULT_PROMPT = """IMAGE ASSET METADATA GENERATION PROMPT (UPDATED)
You are an AI assistant tasked with generating descriptive metadata for visual assets.
MANDATORY OUTPUT FORMAT
- Output exactly TWO lines only.
- Line 1 starts with: Asset Name:
- Line 2 starts with: Tags:
- No explanations, no extra lines, no formatting.
ASSET NAME RULES
- Provide asset names in BOTH English and Arabic.
- Use sentence case.
- Length: 3-4 words per language.
- Do NOT include the word "slide", "■■■■■", or any variation.
- Names must be professional, neutral, and visually descriptive.
TAGS RULES
- Single-line, comma-separated list.
- Tags must be bilingual (English + Arabic).
- Minimum 30 tags per asset.
- Avoid redundancy.
- Use stock-photo style descriptive terms.
KEYWORD CONSISTENCY
When relevant, include terms from the unified keyword list such as:
cover, agenda, timeline, process, table, chart, diagram, dashboard, grid, framework,
kpi, performance, data, infographic, comparison, hierarchy, funnel, matrix,
2 point / two point through 10 point / ten point, multi point, row, column,
bar, line, pie, gauge, light, dark, minimal, corporate, modern.
POINT COUNT RULE
- Always include BOTH numeric and spelled-out variants:
Example: 5 point, five point
VISUAL BASIS ONLY
- Describe ONLY what is visible.
- No assumptions, no inferred context.
LOCATION & IDENTITY
- Do NOT mention countries, cities, or identities unless visually certain.
TONE
- Professional
- Corporate
- Brand-library ready

COLOR & STYLE TAGGING

Do NOT include specific color names (e.g., red, blue, green, hex values) in tags or asset names.

Use style-level descriptors only when visually relevant: light, dark, minimal, monochrome, high contrast, low contrast, muted.

If color is the only differentiator and not essential to identification, omit it entirely.

CONTENT-FIRST TAGGING

Prioritize tags that describe the content shown on the asset over generic element-type tags.

Emphasize what is written/displayed structurally (e.g., agenda layout, timeline steps, KPI panel, comparison columns, table rows/columns, chart type + point count) rather than repeatedly tagging basic shapes or generic objects.

Limit “nature-of-elements” tags (e.g., rectangle, circle, icon, abstract shapes) to a small subset; include them only if they are visually dominant or necessary to distinguish the asset.

Ensure at least 70% of tags are content-structure descriptors aligned with the unified keyword list (e.g., agenda, timeline, process, framework, kpi, dashboard, table, chart, grid, comparison, hierarchy, funnel, matrix, infographic, row, column, multi point, X point + spelled-out).

Describe the content and the visuals in equal measures"""


def _load_env() -> None:
    load_dotenv(BASE_DIR / ".env")
    load_dotenv(BACKEND_DIR / ".env")


@dataclass(frozen=True)
class Settings:
    openai_api_key: str
    openai_model: str
    max_concurrency: int
    max_files: int
    soffice_path: str
    image_max_side: int
    image_jpeg_quality: int
    cors_origins: list[str]


def _parse_origins(raw: str) -> list[str]:
    value = raw.strip()
    if not value:
        return []
    if value == "*":
        return ["*"]
    return [item.strip() for item in value.split(",") if item.strip()]


_load_env()

SETTINGS = Settings(
    openai_api_key=os.getenv("OPENAI_API_KEY", "").strip(),
    openai_model=os.getenv("OPENAI_MODEL", "gpt-5.1").strip(),
    max_concurrency=int(os.getenv("MAX_CONCURRENCY", "6")),
    max_files=int(os.getenv("MAX_FILES", "100")),
    soffice_path=os.getenv("SOFFICE_PATH", "").strip(),
    image_max_side=int(os.getenv("IMAGE_MAX_SIDE", "1280")),
    image_jpeg_quality=int(os.getenv("IMAGE_JPEG_QUALITY", "82")),
    cors_origins=_parse_origins(os.getenv("CORS_ORIGINS", "http://localhost:5173")),
)

DATA_DIR.mkdir(parents=True, exist_ok=True)
