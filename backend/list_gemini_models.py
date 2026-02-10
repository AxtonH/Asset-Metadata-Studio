"""
Quick script to list available Gemini models for your API key.
Run this to see what models you have access to.
"""
import os
from dotenv import load_dotenv
import google.generativeai as genai

# Load environment variables
load_dotenv()

api_key = os.getenv("GOOGLE_API_KEY")
if not api_key:
    print("ERROR: GOOGLE_API_KEY not found in .env file")
    exit(1)

genai.configure(api_key=api_key)

print("Fetching available Gemini models...\n")
try:
    models = genai.list_models()
    
    vision_models = []
    text_models = []
    
    for model in models:
        if 'generateContent' in model.supported_generation_methods:
            model_name = model.name.replace('models/', '') if model.name.startswith('models/') else model.name
            
            # Check if it supports vision (multimodal)
            # Most modern Gemini models support vision, but we can check
            if hasattr(model, 'input_token_limit') and model.input_token_limit:
                vision_models.append(model_name)
            else:
                text_models.append(model_name)
    
    print("=" * 60)
    print("VISION-CAPABLE MODELS (for image analysis):")
    print("=" * 60)
    for model_name in sorted(vision_models):
        print(f"  - {model_name}")
    
    if text_models:
        print("\n" + "=" * 60)
        print("TEXT-ONLY MODELS:")
        print("=" * 60)
        for model_name in sorted(text_models):
            print(f"  - {model_name}")
    
    print("\n" + "=" * 60)
    print("RECOMMENDED FOR YOUR USE CASE:")
    print("=" * 60)
    recommended = [
        "gemini-1.5-flash",  # Good balance of cost and quality
        "gemini-1.5-pro",    # Higher quality
        "gemini-2.5-flash",  # If available
        "gemini-2.5-flash-lite",  # Cheapest option if available
    ]
    
    for rec in recommended:
        if rec in vision_models:
            print(f"  ✓ {rec} - AVAILABLE")
        elif rec in text_models:
            print(f"  ? {rec} - Available but may not support vision")
        else:
            print(f"  ✗ {rec} - NOT AVAILABLE")
    
    print("\n" + "=" * 60)
    print("SET YOUR MODEL:")
    print("=" * 60)
    if vision_models:
        print(f"Set GOOGLE_MODEL={vision_models[0]} in your .env file")
    else:
        print("No vision-capable models found. Check your API key permissions.")
        
except Exception as e:
    print(f"ERROR: {e}")
    print("\nMake sure:")
    print("1. Your GOOGLE_API_KEY is correct")
    print("2. Generative Language API is enabled")
    print("3. Your API key has the right permissions")
