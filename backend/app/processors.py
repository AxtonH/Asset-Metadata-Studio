from __future__ import annotations

import asyncio
import re

from .config import SETTINGS
from .models import AssetResult, AssetTask
from .openai_client import generate_metadata, rewrite_metadata_text
from .parsing import parse_metadata

ARABIC_RE = re.compile(r"[\u0600-\u06FF\u0750-\u077F\u08A0-\u08FF\uFB50-\uFDFF\uFE70-\uFEFF]")


def _has_arabic(value: str) -> bool:
    return bool(ARABIC_RE.search(value or ""))


def _safe_preview(value: str, limit: int = 1200) -> str:
    text = (value or "").strip()
    if len(text) > limit:
        text = text[:limit] + "...<truncated>"
    return text.encode("unicode_escape").decode("ascii")


def _debug(msg: str) -> None:
    if SETTINGS.metadata_debug:
        print(f"[metadata-debug] {msg}", flush=True)


def _normalize_tag_format(tags: str) -> str:
    if not tags:
        return ""
    normalized: list[str] = []
    for raw_tag in tags.split(","):
        tag = raw_tag.strip()
        if not tag:
            continue
        if "/" in tag:
            left, right = [part.strip() for part in tag.split("/", 1)]
            if left and right:
                normalized.extend([left, right])
                continue
        normalized.append(tag)
    return ", ".join(normalized)


def _summarize_tags(tags: str) -> tuple[int, int, int]:
    tag_list = [tag.strip() for tag in tags.split(",") if tag.strip()]
    arabic_count = 0
    latin_count = 0
    for tag in tag_list:
        has_arabic = _has_arabic(tag)
        has_latin = any(("A" <= ch <= "Z") or ("a" <= ch <= "z") for ch in tag)
        if has_arabic:
            arabic_count += 1
        if has_latin:
            latin_count += 1
    return len(tag_list), arabic_count, latin_count


def _needs_rewrite(arabic_name: str, tags: str) -> bool:
    if not _has_arabic(arabic_name):
        return True
    total, arabic_count, latin_count = _summarize_tags(tags)
    if total == 0:
        return True
    if total > 80:
        return True
    min_per_language = max(1, int(total * 0.25))
    return arabic_count < min_per_language or latin_count < min_per_language


async def process_assets(
    tasks: list[AssetTask],
    prompt: str,
    api_key: str,
    model: str,
    max_concurrency: int,
) -> list[AssetResult]:
    if not api_key:
        raise RuntimeError("GOOGLE_API_KEY is not set.")

    semaphore = asyncio.Semaphore(max_concurrency)

    async def _run(task: AssetTask) -> AssetResult:
        try:
            async with semaphore:
                text = await generate_metadata(api_key, task.image_path, prompt, model)

            _debug(
                f"task={task.display_name} raw_chars={len(text)} raw_preview={_safe_preview(text)}"
            )
            english, arabic, tags = parse_metadata(text)
            tags = _normalize_tag_format(tags)
            total_tags, arabic_tags, latin_tags = _summarize_tags(tags)
            _debug(
                f"task={task.display_name} parsed english={english!r} arabic={_safe_preview(arabic, 200)} tags_total={total_tags} tags_with_arabic={arabic_tags} tags_with_latin={latin_tags}"
            )

            if _needs_rewrite(arabic, tags):
                _debug(
                    f"task={task.display_name} rewrite_triggered reason=missing_bilingual_tags"
                )
                rewritten = await rewrite_metadata_text(api_key, model, text)
                _debug(
                    f"task={task.display_name} rewritten_chars={len(rewritten)} rewritten_preview={_safe_preview(rewritten)}"
                )
                rewritten_english, rewritten_arabic, rewritten_tags = parse_metadata(
                    rewritten
                )
                if rewritten_tags:
                    rewritten_tags = _normalize_tag_format(rewritten_tags)
                    english, arabic, tags = (
                        rewritten_english,
                        rewritten_arabic,
                        rewritten_tags,
                    )
                    total_tags, arabic_tags, latin_tags = _summarize_tags(tags)
                    _debug(
                        f"task={task.display_name} rewrite_applied tags_total={total_tags} tags_with_arabic={arabic_tags} tags_with_latin={latin_tags}"
                    )

            # Clean up tags: remove duplicates and limit to reasonable number
            if tags:
                tag_list = [tag.strip() for tag in tags.split(",") if tag.strip()]
                # Remove duplicates while preserving order
                seen = set()
                unique_tags = []
                for tag in tag_list:
                    tag_lower = tag.lower().strip()
                    # Skip if we've seen this tag (case-insensitive)
                    if tag_lower not in seen:
                        seen.add(tag_lower)
                        unique_tags.append(tag)
                # Keep tags aligned to prompt requirement upper bound.
                tags = ", ".join(unique_tags[:40])
            
            return AssetResult(
                task_id=task.task_id,
                display_name=task.display_name,
                english_name=english,
                arabic_name=arabic,
                tags=tags,
                raw_text=text,
            )
        except Exception as exc:
            return AssetResult(
                task_id=task.task_id,
                display_name=task.display_name,
                english_name="",
                arabic_name="",
                tags=f"Error: {exc}",
                raw_text="",
            )

    return await asyncio.gather(*[_run(task) for task in tasks])
