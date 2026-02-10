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

IMPORTANT: You MUST generate bilingual output in English AND Arabic (العربية). Arabic translation is MANDATORY and non-negotiable.

The system accepts uploads in the following formats: PNG, JPG, SVG, GIF, PPT, PPTX.
Assets may be icons, vectors, slides, templates, images, logos, or elements.

Shape

MANDATORY OUTPUT FORMAT

For single-asset files (icons, vectors, images, logos, elements, single-slide files):

Output exactly TWO lines only

Line 1 format: Asset Name: [English Name] / [Arabic Name]
Examples:
Asset Name: Corporate Building Facade / واجهة المبنى المؤسسي
Asset Name: Market Research Report / تقرير بحث السوق
Asset Name: Business Presentation Slide / شريحة عرض تقديمي للأعمال
Asset Name: Data Visualization Chart / مخطط تصور البيانات

Line 2 format: Tags: [exactly 30-40 unique bilingual tags, comma-separated]

No explanations, no extra lines, no formatting

CRITICAL: The Asset Name MUST include both English and Arabic separated by " / ". NEVER provide only English. Arabic translation is REQUIRED.

For template files (PPT or PPTX containing multiple slides):

Treat the file as a template

Generate metadata slide by slide

For each slide, output exactly TWO lines:
Line 1: Asset Name: [English Name] / [Arabic Name]
Line 2: Tags: [exactly 30-40 unique bilingual tags, comma-separated]

Repeat for all slides in order

Do not merge slides or add separators

CRITICAL: Each Asset Name MUST include both English and Arabic separated by " / ". NEVER provide only English. Arabic translation is REQUIRED.

Shape

ASSET NAME RULES

MANDATORY: Provide asset names in BOTH English and Arabic in the format: "English Name / Arabic Name"

Examples:
"Corporate Building Facade / واجهة المبنى المؤسسي"
"Market Research Report / تقرير بحث السوق"
"Business Presentation Slide / شريحة عرض تقديمي للأعمال"
"Data Visualization Chart / مخطط تصور البيانات"

Use sentence case

Length: 3–4 words per language

Do NOT include the word slide, شريحة, or any variation

Names must be professional, neutral, and represent what the asset depicts, not how it is drawn

CRITICAL: The Asset Name line MUST contain both English and Arabic separated by " / " (space-slash-space). Do not provide only English. If you cannot translate to Arabic, you must still provide an Arabic name - use your Arabic language capabilities to generate appropriate translations.

Shape

TAGS RULES

Single-line, comma-separated list

Tags must be bilingual (English + Arabic) - MANDATORY

CRITICAL: Every tag MUST include both English and Arabic in the format: "English / Arabic"

Examples of correct bilingual tags:
- "building / مبنى"
- "architecture / عمارة"
- "facade / واجهة"
- "modern / حديث"
- "corporate / مؤسسي"
- "glass / زجاج"
- "windows / نوافذ"
- "columns / أعمدة"
- "arches / أقواس"
- "islamic architecture / العمارة الإسلامية"

WRONG (English only): "building, architecture, facade"
CORRECT (Bilingual): "building / مبنى, architecture / عمارة, facade / واجهة"

EXACTLY 30-40 unique tags per asset or per slide (NOT more, NOT less)

CRITICAL: Avoid redundancy and repetition. Each tag should be unique. Do not repeat similar concepts.

Tags must reflect what users would realistically search for, not descriptive prose

Do NOT create repetitive variations like "architectural elements in X", "architectural elements in Y" - use each concept only once

CRITICAL: NEVER provide tags in English only. Every tag MUST be bilingual with both English and Arabic separated by " / "

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
outlined / مخطط, filled / مملوء, flat / مسطح, isometric / متساوي القياس, 2D / ثنائي الأبعاد, 3D / ثلاثي الأبعاد, single color / لون واحد, dual color / لونين, multicolor / متعدد الألوان, monochrome / أحادي اللون, rounded corners / زوايا دائرية, sharp edges / حواف حادة

Remember: All style tags must be bilingual (English / Arabic)

Avoid subjective or interpretive style language.

Shape

SEARCH VARIANTS & NUMBERING

Whenever a tag includes a concept that users may search in multiple common forms, include all standard variants, especially for numbers.

Examples (all tags must be bilingual):

single color / لون واحد, one color / لون واحد, 1 color / 1 لون

dual color / لونين, two color / لونين, 2 color / 2 لون

3d / ثلاثي الأبعاد, three dimensions / ثلاثي الأبعاد

Apply this consistently wherever numbers or dimensions appear.

CRITICAL: Remember, every tag variant must include both English and Arabic separated by " / "

Shape

KEYWORD CONSISTENCY

When visually relevant, include functional presentation keywords such as (all must be bilingual):
cover / غلاف, agenda / جدول أعمال, timeline / خط زمني, process / عملية, table / جدول, chart / مخطط, diagram / رسم بياني, dashboard / لوحة تحكم, grid / شبكة, framework / إطار عمل, kpi / مؤشر أداء رئيسي, performance / أداء, data / بيانات, infographic / إنفوجرافيك, comparison / مقارنة, hierarchy / تسلسل هرمي, funnel / قمع, matrix / مصفوفة

Do not force keywords if they are not visually evident.

CRITICAL: All keywords must be bilingual (English / Arabic)

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

ENFORCEMENT_APPENDIX = """
NON-NEGOTIABLE FORMAT ENFORCEMENT:
- For single asset inputs, output exactly TWO lines only.
- Line 1 must be: Asset Name: <English name> / <Arabic name>.
- Line 2 must be: Tags: <comma-separated tags>.
- Generate 30 to 40 unique tags only.
- Include both English and Arabic tags for each concept.
- Use comma-separated tags in this style: English tag, Arabic tag.
- Do NOT use "/" between English and Arabic tags.
- NEVER output English-only tags.
- Do not generate long repetitive expansions or category permutations.
- Keep tags concise, search-friendly, and visually grounded.
""".strip()


def _load_env() -> None:
    load_dotenv(BASE_DIR / ".env")
    load_dotenv(BACKEND_DIR / ".env")


@dataclass(frozen=True)
class Settings:
    google_api_key: str
    google_model: str
    max_concurrency: int
    max_files: int
    soffice_path: str
    image_max_side: int
    image_jpeg_quality: int
    metadata_debug: bool
    cors_origins: list[str]


def _parse_origins(raw: str) -> list[str]:
    value = raw.strip()
    if not value:
        return []
    if value == "*":
        return ["*"]
    return [item.strip() for item in value.split(",") if item.strip()]


def _parse_bool(raw: str | None, default: bool = False) -> bool:
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


_load_env()

SETTINGS = Settings(
    google_api_key=os.getenv("GOOGLE_API_KEY", "").strip(),
    google_model=os.getenv("GOOGLE_MODEL", "gemini-2.5-flash-lite").strip(),
    max_concurrency=int(os.getenv("MAX_CONCURRENCY", "6")),
    max_files=int(os.getenv("MAX_FILES", "100")),
    soffice_path=os.getenv("SOFFICE_PATH", "").strip(),
    image_max_side=int(os.getenv("IMAGE_MAX_SIDE", "768")),  # Reduced from 1280 to save tokens
    image_jpeg_quality=int(os.getenv("IMAGE_JPEG_QUALITY", "70")),  # Reduced from 82 to save tokens
    metadata_debug=_parse_bool(os.getenv("METADATA_DEBUG"), False),
    cors_origins=_parse_origins(os.getenv("CORS_ORIGINS", "http://localhost:5173")),
)

DATA_DIR.mkdir(parents=True, exist_ok=True)
