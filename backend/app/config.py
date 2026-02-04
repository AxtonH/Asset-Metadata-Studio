from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parents[2]
BACKEND_DIR = BASE_DIR / "backend"
DATA_DIR = BACKEND_DIR / "data"
STATIC_DIR = BACKEND_DIR / "static"

DEFAULT_PROMPT = """IMAGE ASSET METADATA GENERATION PROMPT (GENERAL + ASSET GUIDANCE)
You are an AI assistant tasked with generating search-optimized metadata for visual assets used in a professional presentation asset library.

The system accepts uploads in the following formats: PNG, JPG, SVG, GIF, PPT, PPTX.
Assets may be icons, vectors, slides, templates, images, logos, or elements.

Shape

MANDATORY OUTPUT FORMAT

For single-asset files (icons, vectors, images, logos, elements, single-slide files):

Output exactly TWO lines only

Line 1 starts with: Asset Name:

Line 2 starts with: Tags:

No explanations, no extra lines, no formatting

For template files (PPT or PPTX containing multiple slides):

Treat the file as a template

Generate metadata slide by slide

For each slide, output exactly TWO lines using the same format

Repeat for all slides in order

Do not merge slides or add separators

Shape

ASSET NAME RULES

Provide asset names in BOTH English and Arabic

Use sentence case

Length: 3–4 words per language

Do NOT include the word slide, شريحة, or any variation

Names must be professional, neutral, and represent what the asset depicts, not how it is drawn

Shape

TAGS RULES

Single-line, comma-separated list

Tags must be bilingual (English + Arabic)

Minimum 30 tags per asset or per slide

Avoid redundancy

Tags must reflect what users would realistically search for, not descriptive prose

Shape

TAG GENERATION PRINCIPLES

Describe only what is visually recognizable

Use clear, searchable nouns for recognizable subjects or symbols

Visually recognizable symbols are not considered inferred meaning

Avoid interpretive, qualitative, or prose-like tags (e.g. clean lines, grid feel)

Avoid micro-level drawing descriptions

Shape

STYLE TAG GUIDANCE

Use atomic, structural, system-based style attributes that support filtering, such as:
outlined, filled, flat, isometric, 2D, 3D, single color, dual color, multicolor, monochrome, rounded corners, sharp edges

Avoid subjective or interpretive style language.

Shape

SEARCH VARIANTS & NUMBERING

Whenever a tag includes a concept that users may search in multiple common forms, include all standard variants, especially for numbers.

Examples:

single color, one color, 1 color, لون واحد, 1 لون

dual color, two color, 2 color, لونين, 2 لون

3d, three dimensions, ثلاثي الأبعاد

Apply this consistently wherever numbers or dimensions appear.

Shape

KEYWORD CONSISTENCY

When visually relevant, include functional presentation keywords such as:
cover, agenda, timeline, process, table, chart, diagram, dashboard, grid, framework, kpi, performance, data, infographic, comparison, hierarchy, funnel, matrix

Do not force keywords if they are not visually evident.

Shape

LOCATION & IDENTITY

Do not mention countries, cities, organizations, or identities unless explicitly visible.

Shape

TONE

Professional

Corporate

Brand-library ready

Search- and filter-optimized

ASSET-TYPE PRIORITIZATION GUIDANCE (APPLY AFTER THE ABOVE)

Use the following guidance only to prioritize tag types, not to hard-classify assets.

generate metadata slide by slide; prioritize layout, structure, and usage tags.

This guidance should shape emphasis, not introduce new tag types or override visual evidence."""


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
    openai_model=os.getenv("OPENAI_MODEL", "gpt-5-mini").strip(),
    max_concurrency=int(os.getenv("MAX_CONCURRENCY", "6")),
    max_files=int(os.getenv("MAX_FILES", "100")),
    soffice_path=os.getenv("SOFFICE_PATH", "").strip(),
    image_max_side=int(os.getenv("IMAGE_MAX_SIDE", "1280")),
    image_jpeg_quality=int(os.getenv("IMAGE_JPEG_QUALITY", "82")),
    cors_origins=_parse_origins(os.getenv("CORS_ORIGINS", "http://localhost:5173")),
)

DATA_DIR.mkdir(parents=True, exist_ok=True)
