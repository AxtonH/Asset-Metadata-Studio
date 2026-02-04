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
    # Try output_text attribute first
    text = getattr(response, "output_text", None)
    if text:
        return str(text).strip()

    # Try output attribute
    output = getattr(response, "output", None)
    if output:
        chunks = []
        # Handle list of items
        if isinstance(output, list):
            for item in output:
                # Try direct text attribute
                if hasattr(item, "text"):
                    chunks.append(str(item.text))
                # Try content attribute
                content = getattr(item, "content", None)
                if content:
                    if isinstance(content, list):
                        for part in content:
                            part_text = getattr(part, "text", None)
                            if part_text:
                                chunks.append(str(part_text))
                    elif isinstance(content, str):
                        chunks.append(content)
        # Handle single item
        elif hasattr(output, "text"):
            chunks.append(str(output.text))
        elif hasattr(output, "content"):
            content = output.content
            if isinstance(content, list):
                for part in content:
                    part_text = getattr(part, "text", None)
                    if part_text:
                        chunks.append(str(part_text))
            elif isinstance(content, str):
                chunks.append(content)
        
        if chunks:
            return "\n".join(chunks).strip()

    # Try direct text attribute on response
    if hasattr(response, "text"):
        return str(response.text).strip()
    
    # Try to convert response to string if it's a simple type
    if isinstance(response, str):
        return response.strip()
    
    # Last resort: try to get string representation
    return ""


async def generate_metadata(
    client: AsyncOpenAI,
    image_path: Path,
    prompt: str,
    model: str,
) -> str:
    data = base64.b64encode(image_path.read_bytes()).decode("ascii")
    data_url = f"data:{_mime_type(image_path)};base64,{data}"

    # Check if model uses responses API (like gpt-5-mini) or chat completions API
    # GPT-5-mini uses the responses API for vision/image inputs
    use_responses_api = "gpt-5" in model.lower()
    
    if use_responses_api:
        # Use responses API for GPT-5-mini
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
            max_output_tokens=2000,  # Increased to allow for longer responses
        )

        text = _extract_text(response)
        if not text:
            # Provide more detailed error information for debugging
            response_repr = str(response)
            response_attrs = [attr for attr in dir(response) if not attr.startswith("_")]
            error_msg = (
                f"OpenAI response did not include text output. "
                f"Response type: {type(response)}, "
                f"Response attributes: {response_attrs}, "
                f"Response repr: {response_repr[:500]}"
            )
            raise RuntimeError(error_msg)
        return text
    else:
        # Use standard chat.completions API (for other models that don't use responses API)
        # Increase max_completion_tokens to avoid truncation
        response = await client.chat.completions.create(
            model=model,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {
                            "type": "image_url",
                            "image_url": {"url": data_url},
                        },
                    ],
                }
            ],
            max_completion_tokens=2000,  # Increased from 400 to allow for longer responses
        )
        
        # Extract text from chat completions response
        if response.choices and len(response.choices) > 0:
            choice = response.choices[0]
            
            # Check for refusal or other issues
            if hasattr(choice, "message"):
                message = choice.message
                
                # Check for refusal
                if hasattr(message, "refusal") and message.refusal:
                    raise RuntimeError(f"Model refused to generate content: {message.refusal}")
                
                # Try different ways to access the content
                if hasattr(message, "content"):
                    content = message.content
                    if content is not None and content != "":
                        return str(content).strip()
                    # If content is empty but finish_reason is 'length', the response was truncated
                    if hasattr(choice, "finish_reason") and choice.finish_reason == "length":
                        raise RuntimeError(
                            f"Response was truncated (hit token limit). "
                            f"Content was empty. Consider increasing max_completion_tokens or check if the model supports vision/image inputs."
                        )
                
                # Try alternative content access
                if hasattr(message, "text"):
                    text = message.text
                    if text:
                        return str(text).strip()
            
            # Try direct content access on choice
            if hasattr(choice, "content"):
                content = choice.content
                if content:
                    return str(content).strip()
            
            # Try delta (for streaming responses)
            if hasattr(choice, "delta"):
                delta = choice.delta
                if hasattr(delta, "content") and delta.content:
                    return str(delta.content).strip()
            
            # If we get here and finish_reason is 'length' with empty content, it's likely a vision support issue
            if hasattr(choice, "finish_reason"):
                finish_reason = choice.finish_reason
                if finish_reason == "length":
                    raise RuntimeError(
                        "Response was truncated and content is empty. "
                        "This may indicate that GPT-5-mini does not support vision/image inputs. "
                        "Please verify that the model supports image inputs or use a vision-capable model."
                    )
        
        # Fallback: try the general extraction function
        text = _extract_text(response)
        if text:
            return text
        
        # Provide detailed error information for debugging
        response_repr = str(response)
        response_attrs = [attr for attr in dir(response) if not attr.startswith("_")]
        choice_info = ""
        if hasattr(response, "choices") and response.choices:
            choice = response.choices[0]
            choice_attrs = [attr for attr in dir(choice) if not attr.startswith("_")]
            choice_repr = str(choice)
            choice_info = f" Choice attributes: {choice_attrs}, Choice repr: {choice_repr[:500]}"
        
        error_msg = (
            f"Chat completions response did not include text output. "
            f"Response type: {type(response)}, "
            f"Response attributes: {response_attrs}, "
            f"Response repr: {response_repr[:500]},"
            f"{choice_info}"
        )
        raise RuntimeError(error_msg)