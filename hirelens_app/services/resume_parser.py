import json
import PyPDF2
from .llm_engine import query_llm

def extract_text_from_file(file_path):
    """Simple text extractor for PDFs"""
    text = ""
    try:
        if file_path.lower().endswith('.pdf'):
            with open(file_path, 'rb') as f:
                reader = PyPDF2.PdfReader(f)
                for page in reader.pages:
                    text += page.extract_text() + "\n"
        # Add Image logic here if needed (using pytesseract)
    except Exception as e:
        print(f"File Read Error: {e}")
    return text[:8000]  # Truncate to fit context window

def parse_resume_smart(file_path):
    """Uses AI to turn raw resume text into structured JSON"""
    raw_text = extract_text_from_file(file_path)
    
    prompt = f"""
    Analyze this resume text and output a JSON object with these exact keys:
    {{
        "candidate_name": "String",
        "email": "String",
        "phone": "String",
        "skills": ["List", "of", "extracted", "technical", "skills"],
        "experience_years": Integer (estimate based on history, default 0 if unknown),
        "summary": "A 2-sentence professional summary of the candidate"
    }}
    
    RESUME TEXT:
    {raw_text}
    """
    
    response = query_llm(prompt, json_mode=True)
    try:
        return json.loads(response)
    except json.JSONDecodeError:
        return {"skills": [], "summary": "Could not parse resume.", "experience_years": 0}