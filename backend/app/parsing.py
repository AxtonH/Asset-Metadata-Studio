from __future__ import annotations

import re
from typing import Tuple

ARABIC_RE = re.compile(r"[\u0600-\u06FF\u0750-\u077F\u08A0-\u08FF\uFB50-\uFDFF\uFE70-\uFEFF]")
LATIN_RE = re.compile(r"[A-Za-z]")
SEPARATORS = [" - ", " \u2013 ", " \u2014 ", " / ", " \u2022 "]


def _clean_segment(value: str) -> str:
    return value.strip().strip("-\u2013\u2014/|:\u2022").strip()


def _has_arabic(value: str) -> bool:
    return bool(ARABIC_RE.search(value))


def _has_latin(value: str) -> bool:
    return bool(LATIN_RE.search(value))


def _split_bilingual_name(value: str) -> Tuple[str, str]:
    value = " ".join(value.split())
    if not value:
        return "", ""

    if "|" in value:
        left, right = [part.strip() for part in value.split("|", 1)]
        if left and right:
            return left, right

    for separator in SEPARATORS:
        if separator in value:
            left, right = [part.strip() for part in value.split(separator, 1)]
            if not left or not right:
                continue
            left_arabic = _has_arabic(left)
            right_arabic = _has_arabic(right)
            if left_arabic != right_arabic:
                if right_arabic:
                    return _clean_segment(left), _clean_segment(right)
                return _clean_segment(right), _clean_segment(left)

    if not _has_arabic(value):
        return _clean_segment(value), ""
    if not _has_latin(value):
        return "", _clean_segment(value)

    first_arabic = ARABIC_RE.search(value)
    first_latin = LATIN_RE.search(value)
    if not first_arabic or not first_latin:
        return _clean_segment(value), ""

    if first_latin.start() < first_arabic.start():
        english = value[: first_arabic.start()]
        arabic = value[first_arabic.start() :]
        return _clean_segment(english), _clean_segment(arabic)

    arabic = value[: first_latin.start()]
    english = value[first_latin.start() :]
    return _clean_segment(english), _clean_segment(arabic)


def parse_metadata(text: str) -> Tuple[str, str, str]:
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    asset_line = ""
    tags_line = ""

    for line in lines:
        if line.lower().startswith("asset name:"):
            asset_line = line
        elif line.lower().startswith("tags:"):
            tags_line = line

    asset_value = asset_line.split(":", 1)[1].strip() if ":" in asset_line else ""
    tags_value = tags_line.split(":", 1)[1].strip() if ":" in tags_line else ""

    english, arabic = _split_bilingual_name(asset_value)

    return english, arabic, tags_value
