from __future__ import annotations

import logging
from pathlib import Path

from google import genai
from google.genai import types

logger = logging.getLogger(__name__)

BILINGUAL_SYSTEM_INSTRUCTION = (
    "You MUST generate bilingual output in English AND Arabic (العربية). "
    "Every Asset Name MUST include both English and Arabic separated by ' / '. "
    "Tags must be comma-separated and include both English and Arabic terms. "
    "For each concept, include both forms as separate tags (example: building, مبنى). "
    "Do NOT use '/' between English and Arabic tags. "
    "Arabic translation is MANDATORY for both names and tags. Never provide only English."
)

REWRITE_PROMPT_TEMPLATE = """
Rewrite the metadata below to the exact required format.

Rules:
- Output exactly TWO lines only.
- Line 1: Asset Name: <English name> / <Arabic name>
- Line 2: Tags: <comma-separated tags>
- Generate 30 to 40 unique tags.
- Include both English and Arabic tags.
- For each concept, provide English then Arabic as separate tags, comma-separated.
- Example: building, مبنى, architecture, عمارة
- Do NOT output English-only tags.
- Do NOT use '/' between English and Arabic tags.
- Keep only the best visually relevant tags.
- Do not add explanations.

Metadata to rewrite:
{raw}
""".strip()


def _mime_type(path: Path) -> str:
    ext = path.suffix.lower()
    if ext in {".jpg", ".jpeg"}:
        return "image/jpeg"
    if ext == ".gif":
        return "image/gif"
    return "image/png"


def _extract_response_text(response: object) -> str:
    # Primary path for google.genai GenerateContentResponse
    if response and hasattr(response, "text"):
        text = getattr(response, "text", None)
        if text:
            return str(text).strip()

    # Fallback path: iterate candidate parts
    if response and hasattr(response, "candidates"):
        candidates = getattr(response, "candidates", None) or []
        if candidates:
            candidate = candidates[0]
            if hasattr(candidate, "content"):
                content = candidate.content
                if hasattr(content, "parts"):
                    text_parts = []
                    for part in content.parts or []:
                        if hasattr(part, "text") and part.text:
                            text_parts.append(part.text)
                    if text_parts:
                        return "\n".join(text_parts).strip()
    return ""


async def _generate_content_text(
    api_key: str,
    model: str,
    contents: list[dict],
    max_output_tokens: int,
    temperature: float,
) -> str:
    client = genai.Client(api_key=api_key)
    async_client = client.aio
    try:
        response = await async_client.models.generate_content(
            model=model,
            contents=contents,
            config=types.GenerateContentConfig(
                max_output_tokens=max_output_tokens,
                temperature=temperature,
                system_instruction=BILINGUAL_SYSTEM_INSTRUCTION,
            ),
        )
        text = _extract_response_text(response)
        if text:
            return text

        if response and hasattr(response, "prompt_feedback"):
            feedback = response.prompt_feedback
            if feedback and hasattr(feedback, "block_reason") and feedback.block_reason:
                raise RuntimeError(
                    f"Content was blocked. Reason: {feedback.block_reason}. "
                    f"Safety ratings: {getattr(feedback, 'safety_ratings', 'N/A')}"
                )
        raise RuntimeError("Gemini response did not include text output.")
    except Exception as e:
        error_msg = str(e)
        if "not found" in error_msg.lower() or "404" in error_msg:
            try:
                models_list = await async_client.models.list()
                model_names = []
                for m in models_list:
                    if hasattr(m, "name"):
                        model_name = (
                            m.name.replace("models/", "")
                            if m.name.startswith("models/")
                            else m.name
                        )
                        model_names.append(model_name)
                if model_names:
                    raise RuntimeError(
                        f"Model '{model}' not found. Available models: {', '.join(model_names[:10])}. "
                        f"Please set GOOGLE_MODEL to one of these models in your .env file. "
                        f"Original error: {error_msg}"
                    ) from e
            except Exception as list_err:
                raise RuntimeError(
                    f"Model '{model}' not found. Could not list available models: {list_err}. "
                    f"Try 'gemini-2.5-flash-lite' or 'gemini-2.5-flash'. "
                    f"Original error: {error_msg}"
                ) from e
        if "API key" in error_msg or "authentication" in error_msg.lower():
            raise RuntimeError(
                f"Google API authentication error: {error_msg}. "
                "Please check your GOOGLE_API_KEY in the .env file."
            ) from e
        if "quota" in error_msg.lower() or "rate limit" in error_msg.lower():
            raise RuntimeError(
                f"Google API quota/rate limit exceeded: {error_msg}. "
                "Please check your usage limits in Google AI Studio."
            ) from e
        raise RuntimeError(f"Gemini API error: {error_msg}") from e
    finally:
        await async_client.aclose()


async def generate_metadata(
    api_key: str,
    image_path: Path,
    prompt: str,
    model: str,
) -> str:
    """
    Generate metadata using Google Gemini API (google.genai package).
    
    Args:
        api_key: Google API key
        image_path: Path to the image file
        prompt: The prompt text
        model: Model name (e.g., 'gemini-2.5-flash-lite')
    
    Returns:
        Generated text response
    """
    if not api_key:
        raise RuntimeError("GOOGLE_API_KEY is not set.")
    
    # Normalize the model name (remove models/ prefix if present)
    model = model.replace('models/', '') if model.startswith('models/') else model
    
    image_data = image_path.read_bytes()
    contents = [
        {"text": prompt},
        {
            "inline_data": {
                "mime_type": _mime_type(image_path),
                "data": image_data,
            }
        },
    ]
    return await _generate_content_text(
        api_key=api_key,
        model=model,
        contents=contents,
        max_output_tokens=1600,
        temperature=0.2,
    )


async def rewrite_metadata_text(
    api_key: str,
    model: str,
    raw_text: str,
) -> str:
    if not raw_text.strip():
        return raw_text
    model = model.replace("models/", "") if model.startswith("models/") else model
    contents = [{"text": REWRITE_PROMPT_TEMPLATE.format(raw=raw_text.strip())}]
    rewritten = await _generate_content_text(
        api_key=api_key,
        model=model,
        contents=contents,
        max_output_tokens=1200,
        temperature=0.1,
    )
    logger.debug("Metadata rewrite applied (chars=%s).", len(rewritten))
    return rewritten
