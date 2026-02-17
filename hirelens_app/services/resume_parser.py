# import json
# import PyPDF2
# from .llm_engine import query_llm

# def extract_text_from_file(file_path):
#     """Simple text extractor for PDFs"""
#     text = ""
#     try:
#         if file_path.lower().endswith('.pdf'):
#             with open(file_path, 'rb') as f:
#                 reader = PyPDF2.PdfReader(f)
#                 for page in reader.pages:
#                     text += page.extract_text() + "\n"
#         # Add Image logic here if needed (using pytesseract)
#     except Exception as e:
#         print(f"File Read Error: {e}")
#     return text[:8000]  # Truncate to fit context window

# def parse_resume_smart(file_path):
#     """Uses AI to turn raw resume text into structured JSON"""
#     raw_text = extract_text_from_file(file_path)
    
#     prompt = f"""
#     Analyze this resume text and output a JSON object with these exact keys:
#     {{
#         "candidate_name": "String",
#         "email": "String",
#         "phone": "String",
#         "skills": ["List", "of", "extracted", "technical", "skills"],
#         "experience_years": Integer (estimate based on history, default 0 if unknown),
#         "summary": "A 2-sentence professional summary of the candidate"
#     }}
    
#     RESUME TEXT:
#     {raw_text}
#     """
    
#     response = query_llm(prompt, json_mode=True)
#     try:
#         return json.loads(response)
#     except json.JSONDecodeError:
#         return {"skills": [], "summary": "Could not parse resume.", "experience_years": 0}


# hirelens_app/services/resume_parser.py

# hirelens_app/services/resume_parser.py

import google.generativeai as genai
from django.conf import settings
import pdfplumber
import json
import re

genai.configure(api_key=settings.GEMINI_API_KEY)

def extract_text_from_file(file_path):
    text = ""
    try:
        if file_path.endswith('.pdf'):
            with pdfplumber.open(file_path) as pdf:
                for page in pdf.pages:
                    text += (page.extract_text() or "") + "\n"
        else:
            with open(file_path, 'r', errors='ignore') as f:
                text = f.read()
    except Exception as e:
        print(f"❌ File Read Error: {e}")
    return text

def clean_json_string(text):
    if not text: return ""
    cleaned = text.replace("```json", "").replace("```", "").strip()
    try:
        if '{' in cleaned:
            start = cleaned.find('{')
            end = cleaned.rfind('}') + 1
            return cleaned[start:end]
    except: pass
    return cleaned

def parse_resume_smart(file_path):
    text = extract_text_from_file(file_path)
    if not text:
        return {"skills": [], "summary": "Error: Empty file.", "experience_years": 0}

    prompt = f"""
    Extract these details from the resume below in raw JSON format:
    1. "skills": List of technical skills (strings).
    2. "summary": Brief professional summary (string).
    3. "experience_years": Integer estimate of total years.

    RESUME:
    {text[:15000]}
    
    Return ONLY JSON.
    """

    # 🔥 Priority List
    models_to_try = [
        'gemini-2.5-flash-preview-05-20',
        'gemini-2.5-flash-preview-09-2025',
        'gemini-2.0-flash',
        'gemini-1.5-flash'
    ]

    for model_name in models_to_try:
        try:
            model = genai.GenerativeModel(model_name)
            response = model.generate_content(prompt)
            return json.loads(clean_json_string(response.text))
        except Exception as e:
            if "429" in str(e) or "404" in str(e) or "quota" in str(e).lower():
                continue # Try next model quietly
            print(f"Error parsing with {model_name}: {e}")

    return {"skills": ["Manual Review"], "summary": "AI Busy. Try again in 1 min.", "experience_years": 0}