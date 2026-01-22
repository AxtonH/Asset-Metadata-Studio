from __future__ import annotations

import unicodedata
from dataclasses import replace
from typing import List

from .models import AssetResult

ARABIC_LETTER_MAP = str.maketrans(
    {
        "\u0622": "\u0627",  # ALEF WITH MADDA ABOVE -> ALEF
        "\u0623": "\u0627",  # ALEF WITH HAMZA ABOVE -> ALEF
        "\u0625": "\u0627",  # ALEF WITH HAMZA BELOW -> ALEF
        "\u0671": "\u0627",  # ALEF WASLA -> ALEF
        "\u0649": "\u064a",  # ALEF MAKSURA -> YEH
        "\u0624": "\u0648",  # WAW WITH HAMZA -> WAW
        "\u0626": "\u064a",  # YEH WITH HAMZA -> YEH
        "\u0629": "\u0647",  # TEH MARBUTA -> HEH
        "\u0640": "",        # TATWEEL
    }
)

ARABIC_DIGITS_MAP = str.maketrans(
    {
        "\u0660": "0",
        "\u0661": "1",
        "\u0662": "2",
        "\u0663": "3",
        "\u0664": "4",
        "\u0665": "5",
        "\u0666": "6",
        "\u0667": "7",
        "\u0668": "8",
        "\u0669": "9",
        "\u06f0": "0",
        "\u06f1": "1",
        "\u06f2": "2",
        "\u06f3": "3",
        "\u06f4": "4",
        "\u06f5": "5",
        "\u06f6": "6",
        "\u06f7": "7",
        "\u06f8": "8",
        "\u06f9": "9",
    }
)


def _normalize_key(value: str) -> str:
    value = unicodedata.normalize("NFKC", value)
    value = value.translate(ARABIC_LETTER_MAP).translate(ARABIC_DIGITS_MAP)
    value = value.casefold()

    normalized_chars = []
    for char in value:
        category = unicodedata.category(char)
        if category in {"Mn", "Me", "Cf"}:
            continue
        if category.startswith(("L", "N")):
            normalized_chars.append(char)
            continue
        if char.isspace():
            normalized_chars.append(" ")
            continue
        normalized_chars.append(" ")

    return " ".join("".join(normalized_chars).split()).strip()


def _clean_base(value: str) -> str:
    return " ".join(value.split()).strip()


def _apply_suffixes(names: List[str]) -> List[str]:
    keys = [_normalize_key(name) for name in names]
    counts: dict[str, int] = {}
    for key in keys:
        if not key:
            continue
        counts[key] = counts.get(key, 0) + 1

    seen: dict[str, int] = {}
    updated: List[str] = []
    for original, key in zip(names, keys):
        base = _clean_base(original)
        if not base or counts.get(key, 0) <= 1:
            updated.append(base)
            continue
        seen[key] = seen.get(key, 0) + 1
        updated.append(f"{base} - {seen[key]:03d}")
    return updated


def apply_duplicate_suffixes(results: List[AssetResult]) -> List[AssetResult]:
    english_names = [result.english_name or "" for result in results]
    arabic_names = [result.arabic_name or "" for result in results]

    updated_english = _apply_suffixes(english_names)
    updated_arabic = _apply_suffixes(arabic_names)

    updated_results: List[AssetResult] = []
    for result, english, arabic in zip(results, updated_english, updated_arabic):
        updated_results.append(
            replace(result, english_name=english, arabic_name=arabic)
        )
    return updated_results
