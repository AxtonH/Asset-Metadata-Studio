from __future__ import annotations

import base64
from pathlib import Path
from typing import Any

from openai import AsyncOpenAI


def _mime_type(path: Path) -> str:
    ext = path.suffix.lower()
    if ext in {".jpg", ".jpeg"}:
        return "image/jpeg"
    if ext == ".gif":
        return "image/gif"
    return "image/png"


def _extract_text(response: Any) -> str:
    text = getattr(response, "output_text", "")
    if text:
        return text.strip()

    output = getattr(response, "output", None)
    if not output:
        return ""

    chunks = []
    for item in output:
        content = getattr(item, "content", None)
        if not content:
            continue
        for part in content:
            part_text = getattr(part, "text", None)
            if part_text:
                chunks.append(part_text)
    return "\n".join(chunks).strip()


async def generate_metadata(
    client: AsyncOpenAI,
    image_path: Path,
    prompt: str,
    model: str,
) -> str:
    data = base64.b64encode(image_path.read_bytes()).decode("ascii")
    data_url = f"data:{_mime_type(image_path)};base64,{data}"

    response = await client.responses.create(
        model=model,
        input=[
            {
                "role": "user",
                "content": [
                    {"type": "input_text", "text": prompt},
                    {"type": "input_image", "image_url": data_url},
                ],
            }
        ],
        temperature=0.2,
        max_output_tokens=400,
    )

    text = _extract_text(response)
    if not text:
        raise RuntimeError("OpenAI response did not include text output.")
    return text