# # hirelens_app/services/llm_engine.py
# import os
# import json
# from openai import OpenAI
# from django.conf import settings

# # Initialize Client (It automatically looks for OPENAI_API_KEY in env vars)
# client = OpenAI(api_key=settings.OPENAI_API_KEY)

# def query_llm(prompt: str, json_mode: bool = False) -> str:
#     """
#     Centralized function to query OpenAI GPT.
#     Handles JSON enforcement and error safety.
#     """
#     try:
#         # 1. Select Model (gpt-4o-mini is best for speed/cost balance)
#         model = "gpt-4o-mini" 

#         # 2. Define messages
#         messages = [
#             {"role": "system", "content": "You are a helpful AI assistant for a hiring platform."},
#             {"role": "user", "content": prompt}
#         ]

#         # 3. Call API
#         # If json_mode is True, we force OpenAI to return valid JSON object
#         response = client.chat.completions.create(
#             model=model,
#             messages=messages,
#             response_format={"type": "json_object"} if json_mode else {"type": "text"},
#             temperature=0.7
#         )

#         return response.choices[0].message.content

#     except Exception as e:
#         print(f"❌ OpenAI API Error: {str(e)}")
#         # Return empty JSON object on failure if mode is JSON, else error string
#         return "{}" if json_mode else "Error processing request."

import google.generativeai as genai
from django.conf import settings
import time

# Configure Gemini
genai.configure(api_key=settings.GEMINI_API_KEY)

def query_llm(prompt):
    """
    Sends a prompt to Google Gemini with AUTO-FALLBACK.
    """
    # 🔥 Priority: Your requested model -> Newer Flash -> Stable Pro
    models_to_try = [
        'gemini-2.5-flash-preview-05-20',   # Your requested model
        'gemini-2.5-flash-preview-09-2025', # Backup from your allowed list
        'gemini-3-flash-preview',                 # Fast & Stable backup
        'gemini-1.5-flash'                  # Ultimate fallback
    ]
    
    last_error = ""

    for model_name in models_to_try:
        try:
            model = genai.GenerativeModel(model_name)
            response = model.generate_content(prompt)
            return response.text.strip()
            
        except Exception as e:
            error_msg = str(e).lower()
            # If rate limit (429) or not found (404), try next model
            if "429" in error_msg or "404" in error_msg or "quota" in error_msg or "not found" in error_msg:
                print(f"⚠️ {model_name} unavailable ({error_msg[:30]}...). Switching...")
                last_error = str(e)
                continue
            else:
                print(f"❌ Critical Gemini Error: {e}")
                return ""
                
    print(f"❌ All models failed. Last error: {last_error}")
    return ""