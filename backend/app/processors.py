from __future__ import annotations

import asyncio

from openai import AsyncOpenAI

from .models import AssetResult, AssetTask
from .openai_client import generate_metadata
from .parsing import parse_metadata


async def process_assets(
    tasks: list[AssetTask],
    prompt: str,
    api_key: str,
    model: str,
    max_concurrency: int,
) -> list[AssetResult]:
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY is not set.")

    client = AsyncOpenAI(api_key=api_key)
    semaphore = asyncio.Semaphore(max_concurrency)

    async def _run(task: AssetTask) -> AssetResult:
        try:
            async with semaphore:
                text = await generate_metadata(client, task.image_path, prompt, model)
            english, arabic, tags = parse_metadata(text)
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
