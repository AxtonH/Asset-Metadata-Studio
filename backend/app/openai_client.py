from __future__ import annotations

import base64
import json
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
    # Try output_text attribute FIRST (this is the main text output for responses API)
    # This should be checked before dict conversion to avoid issues
    if hasattr(response, "output_text"):
        text = getattr(response, "output_text", None)
        if text is not None and text != "":
            return str(text).strip()
    
    # Then try to convert response to dict if it's a Pydantic model
    response_dict = None
    if hasattr(response, "model_dump"):
        try:
            response_dict = response.model_dump()
        except Exception:
            pass
    elif hasattr(response, "dict"):
        try:
            response_dict = response.dict()
        except Exception:
            pass
    
    # If we have a dict representation, try extracting from it
    if response_dict:
        # Try output_text first (this is the main text output)
        if "output_text" in response_dict and response_dict["output_text"]:
            return str(response_dict["output_text"]).strip()
        
        # Try output array - look for text content in output items (fallback)
        if "output" in response_dict:
            output = response_dict["output"]
            if isinstance(output, list) and len(output) > 0:
                # Look for message objects with text content
                texts = []
                for item in output:
                    if isinstance(item, dict):
                        # Check if it's a message with content array
                        if item.get("type") == "message" and "content" in item:
                            content = item["content"]
                            if isinstance(content, list):
                                for content_item in content:
                                    if isinstance(content_item, dict) and content_item.get("type") == "output_text":
                                        text_content = content_item.get("text")
                                        if text_content:
                                            texts.append(str(text_content))
                        # Check various other possible text fields
                        item_text = (
                            item.get("text") or 
                            item.get("content") or 
                            item.get("output_text") or
                            item.get("text_content")
                        )
                        if item_text and isinstance(item_text, str):
                            texts.append(item_text)
                    elif isinstance(item, str):
                        texts.append(item)
                if texts:
                    return "\n".join(texts).strip()
            elif isinstance(output, str):
                return output.strip()
            elif isinstance(output, dict):
                output_text = output.get("text") or output.get("content") or output.get("output_text")
                if output_text:
                    return str(output_text).strip()

    # Try output attribute (structured output) - fallback if output_text not available
    output = getattr(response, "output", None)
    if output:
        chunks = []
        # Handle list of items
        if isinstance(output, list):
            for item in output:
                # Check if it's a message object with content
                if hasattr(item, "type") and getattr(item, "type", None) == "message":
                    if hasattr(item, "content"):
                        content = getattr(item, "content", None)
                        if isinstance(content, list):
                            for content_item in content:
                                # Check for output_text type content
                                if hasattr(content_item, "type") and getattr(content_item, "type", None) == "output_text":
                                    if hasattr(content_item, "text"):
                                        text_val = getattr(content_item, "text", None)
                                        if text_val:
                                            chunks.append(str(text_val))
                                # Fallback: try text attribute
                                elif hasattr(content_item, "text"):
                                    text_val = getattr(content_item, "text", None)
                                    if text_val:
                                        chunks.append(str(text_val))
                # Try direct text attribute
                elif hasattr(item, "text"):
                    text_val = getattr(item, "text", None)
                    if text_val:
                        chunks.append(str(text_val))
                # Try content attribute
                elif hasattr(item, "content"):
                    content = getattr(item, "content", None)
                    if isinstance(content, list):
                        for part in content:
                            # Try text attribute
                            part_text = getattr(part, "text", None)
                            if part_text:
                                chunks.append(str(part_text))
                            # Try direct string content
                            elif isinstance(part, str):
                                chunks.append(part)
                    elif isinstance(content, str):
                        chunks.append(content)
                # Try accessing as dict
                elif isinstance(item, dict):
                    # Check for message type with content array
                    if item.get("type") == "message" and "content" in item:
                        for content_item in item["content"]:
                            if isinstance(content_item, dict) and content_item.get("type") == "output_text":
                                text_content = content_item.get("text")
                                if text_content:
                                    chunks.append(str(text_content))
                    else:
                        item_text = item.get("text") or item.get("content") or item.get("output_text")
                        if item_text:
                            chunks.append(str(item_text))
        # Handle single item (not a list)
        elif hasattr(output, "text"):
            text_val = getattr(output, "text", None)
            if text_val:
                chunks.append(str(text_val))
        elif hasattr(output, "content"):
            content = output.content
            if isinstance(content, list):
                for part in content:
                    part_text = getattr(part, "text", None)
                    if part_text:
                        chunks.append(str(part_text))
                    elif isinstance(part, str):
                        chunks.append(part)
            elif isinstance(content, str):
                chunks.append(content)
        # Try accessing output as dict
        elif isinstance(output, dict):
            output_text = output.get("text") or output.get("content") or output.get("output_text")
            if output_text:
                chunks.append(str(output_text))
        
        if chunks:
            return "\n".join(chunks).strip()

    # Try direct text attribute on response
    if hasattr(response, "text"):
        text_val = getattr(response, "text", None)
        if text_val:
            return str(text_val).strip()
    
    # Try accessing response as dict
    if isinstance(response, dict):
        response_text = response.get("text") or response.get("content") or response.get("output_text")
        if response_text:
            return str(response_text).strip()
    
    # Try accessing nested structures recursively
    # Check if response has any string-like attributes
    for attr_name in dir(response):
        if attr_name.startswith("_"):
            continue
        try:
            attr_value = getattr(response, attr_name)
            if isinstance(attr_value, str) and attr_value.strip():
                # Skip common non-content attributes
                if attr_name.lower() not in ["id", "object", "created", "model", "type"]:
                    return attr_value.strip()
        except Exception:
            continue
    
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

    # Check if model uses responses API (like gpt-5-mini, gpt-5-image-mini, gpt-5.1) or chat completions API
    # GPT-5 models use the responses API for vision/image inputs
    use_responses_api = "gpt-5" in model.lower()
    
    if use_responses_api:
        # Use responses API for GPT-5 models (including GPT-5-mini and GPT-5-image-mini)
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
            max_output_tokens=16000,  # Increased significantly to avoid truncation (reasoning + output)
        )
        
        # Check if response is incomplete
        if hasattr(response, "status") and response.status == "incomplete":
            incomplete_reason = ""
            if hasattr(response, "incomplete_details") and response.incomplete_details:
                if hasattr(response.incomplete_details, "reason"):
                    incomplete_reason = response.incomplete_details.reason
            print(f"WARNING: Response is incomplete. Reason: {incomplete_reason}")
            # Try to extract partial text anyway

        # Debug: Print response structure
        print(f"DEBUG: Response type: {type(response)}")
        print(f"DEBUG: Response attributes: {[attr for attr in dir(response) if not attr.startswith('_')]}")
        
        # Try to get full response as dict
        try:
            if hasattr(response, "model_dump"):
                response_dict = response.model_dump()
                print(f"DEBUG: Response dict keys: {list(response_dict.keys())}")
                print(f"DEBUG: Full response dict: {json.dumps(response_dict, indent=2, default=str)}")
        except Exception as e:
            print(f"DEBUG: Could not convert to dict: {e}")
        
        text = _extract_text(response)
        print(f"DEBUG: Extracted text length: {len(text) if text else 0}")
        print(f"DEBUG: Extracted text preview: {text[:200] if text else 'EMPTY'}")
        print(f"DEBUG: output_text attribute: {getattr(response, 'output_text', 'NOT FOUND')}")
        print(f"DEBUG: output attribute type: {type(getattr(response, 'output', None))}")
        print(f"DEBUG: output attribute value: {getattr(response, 'output', None)}")
        
        if not text:
            # Check if response is incomplete - if so, we might still be able to get partial text
            status = getattr(response, "status", None)
            if status == "incomplete":
                # For incomplete responses, output_text might be None
                # But we should still try to get any available text
                # Check if there's any way to get partial results
                error_msg = (
                    f"OpenAI response is incomplete (status: incomplete). "
                    f"The response hit the max_output_tokens limit (8000 tokens). "
                    f"Please increase max_output_tokens or simplify the prompt. "
                    f"Response output_text: {getattr(response, 'output_text', None)}, "
                    f"Output array length: {len(getattr(response, 'output', [])) if hasattr(response, 'output') else 0}"
                )
                raise RuntimeError(error_msg)
            
            # Provide more detailed error information for debugging
            response_repr = str(response)
            response_attrs = [attr for attr in dir(response) if not attr.startswith("_")]
            
            # Try to get more details about the response structure
            output_info = ""
            if hasattr(response, "output"):
                output = response.output
                output_type = type(output)
                output_repr = str(output)[:500]
                output_info = f" Output type: {output_type}, Output repr: {output_repr}"
            
            # Try to convert to dict for better inspection
            try:
                if hasattr(response, "model_dump"):
                    response_dict = response.model_dump()
                    response_json = json.dumps(response_dict, indent=2, default=str)[:2000]
                    output_info += f" Response as dict: {response_json}"
            except Exception:
                pass
            
            error_msg = (
                f"OpenAI response did not include text output. "
                f"Response type: {type(response)}, "
                f"Response status: {status}, "
                f"Response attributes: {response_attrs}, "
                f"Response repr: {response_repr[:500]},"
                f"{output_info}"
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