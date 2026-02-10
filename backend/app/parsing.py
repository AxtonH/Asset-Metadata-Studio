from __future__ import annotations

import re
from typing import Tuple

ARABIC_RE = re.compile(r"[\u0600-\u06FF\u0750-\u077F\u08A0-\u08FF\uFB50-\uFDFF\uFE70-\uFEFF]")
LATIN_RE = re.compile(r"[A-Za-z]")
SEPARATORS = [" - ", " \u2013 ", " \u2014 ", " / ", " \u2022 ", " /", "/ ", " | ", "|"]
TAG_SPLIT_RE = re.compile(r"[,،]")


def _clean_segment(value: str) -> str:
    return value.strip().strip("-\u2013\u2014/|:\u2022").strip()


def _has_arabic(value: str) -> bool:
    return bool(ARABIC_RE.search(value))


def _has_latin(value: str) -> bool:
    return bool(LATIN_RE.search(value))


def _split_tags(value: str) -> list[str]:
    if not value:
        return []
    tags: list[str] = []
    for part in TAG_SPLIT_RE.split(value):
        cleaned = _clean_segment(part)
        if cleaned:
            tags.append(cleaned)
    return tags


def _merge_tag_lines(primary_line: str, continuation_lines: list[str]) -> str:
    primary_tags = _split_tags(primary_line)
    extra_tags = _split_tags(", ".join(continuation_lines))
    if not continuation_lines:
        return ", ".join(primary_tags)
    if not primary_tags:
        return ", ".join(extra_tags)
    if not extra_tags:
        return ", ".join(primary_tags)

    # Gemini sometimes emits English tags after "Tags:" and Arabic tags on the next line.
    # If that pattern is detected, pair tags by index to recover bilingual entries.
    primary_latin_only = sum(
        1 for tag in primary_tags if _has_latin(tag) and not _has_arabic(tag)
    )
    extra_arabic_only = sum(
        1 for tag in extra_tags if _has_arabic(tag) and not _has_latin(tag)
    )
    if (
        primary_latin_only >= max(1, len(primary_tags) // 2)
        and extra_arabic_only >= max(1, len(extra_tags) // 2)
    ):
        pair_count = min(len(primary_tags), len(extra_tags))
        paired = [f"{primary_tags[i]} / {extra_tags[i]}" for i in range(pair_count)]
        if len(primary_tags) > pair_count:
            paired.extend(primary_tags[pair_count:])
        if len(extra_tags) > pair_count:
            paired.extend(extra_tags[pair_count:])
        return ", ".join(paired)

    return ", ".join([*primary_tags, *extra_tags])


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
    tags_line_index = -1

    for index, line in enumerate(lines):
        if line.lower().startswith("asset name:"):
            asset_line = line
        elif line.lower().startswith("tags:"):
            tags_line = line
            tags_line_index = index

    asset_value = asset_line.split(":", 1)[1].strip() if ":" in asset_line else ""
    tags_value = tags_line.split(":", 1)[1].strip() if ":" in tags_line else ""

    continuation_lines: list[str] = []
    if tags_line_index >= 0:
        for next_line in lines[tags_line_index + 1 :]:
            lowered = next_line.lower()
            if lowered.startswith("asset name:") or lowered.startswith("tags:"):
                break
            # Continue only when the line still looks like tag content.
            if "," in next_line or "،" in next_line:
                continuation_lines.append(next_line)
                continue
            if _has_arabic(next_line) and not _has_latin(next_line):
                continuation_lines.append(next_line)
                continue
            break
    tags_value = _merge_tag_lines(tags_value, continuation_lines)

    # If no Arabic found in asset name, check if there are multiple "Asset Name:" lines
    # or if Arabic is on a separate line
    if asset_value and not _has_arabic(asset_value):
        # Look for Arabic text in subsequent lines that might be the Arabic name
        asset_line_index = None
        for i, line in enumerate(lines):
            if line.lower().startswith("asset name:"):
                asset_line_index = i
                break
        
        # Check next few lines for Arabic text that might be the Arabic name
        if asset_line_index is not None and asset_line_index + 1 < len(lines):
            next_line = lines[asset_line_index + 1]
            # If next line has Arabic and doesn't start with "Tags:", it might be the Arabic name
            if _has_arabic(next_line) and not next_line.lower().startswith("tags:"):
                # Combine English and Arabic
                asset_value = f"{asset_value} / {next_line}"
    
    english, arabic = _split_bilingual_name(asset_value)

    return english, arabic, tags_value
