# hirelens_app/services/llm_engine.py
import os
import json
from openai import OpenAI
from django.conf import settings

# Initialize Client (It automatically looks for OPENAI_API_KEY in env vars)
client = OpenAI(api_key=settings.OPENAI_API_KEY)

def query_llm(prompt: str, json_mode: bool = False) -> str:
    """
    Centralized function to query OpenAI GPT.
    Handles JSON enforcement and error safety.
    """
    try:
        # 1. Select Model (gpt-4o-mini is best for speed/cost balance)
        model = "gpt-4o-mini" 

        # 2. Define messages
        messages = [
            {"role": "system", "content": "You are a helpful AI assistant for a hiring platform."},
            {"role": "user", "content": prompt}
        ]

        # 3. Call API
        # If json_mode is True, we force OpenAI to return valid JSON object
        response = client.chat.completions.create(
            model=model,
            messages=messages,
            response_format={"type": "json_object"} if json_mode else {"type": "text"},
            temperature=0.7
        )

        return response.choices[0].message.content

    except Exception as e:
        print(f"❌ OpenAI API Error: {str(e)}")
        # Return empty JSON object on failure if mode is JSON, else error string
        return "{}" if json_mode else "Error processing request."