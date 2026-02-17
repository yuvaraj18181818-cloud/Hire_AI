# import json
# from .llm_engine import query_llm

# def generate_ai_questions(skills, job_role, experience_level):
#     """Generates 5 unique interview questions based on candidate skills"""
    
#     prompt = f"""
#     Generate 5 technical interview questions for a '{job_role}' position.
#     Candidate Skills: {', '.join(skills)}.
#     Experience Level: {experience_level} years.
    
#     Output strictly a JSON array:
#     {{
#         "questions": [
#             {{ "text": "Question 1", "difficulty": "Medium", "topic": "SkillName" }},
#             {{ "text": "Question 2", "difficulty": "Hard", "topic": "SkillName" }}
#         ]
#     }}
#     """
    
#     res = query_llm(prompt, json_mode=True)
#     try:
#         data = json.loads(res)
#         return data.get("questions", [])
#     except:
#         return []

# def evaluate_answer(question_text, candidate_answer):
#     """Grades the answer"""
    
#     prompt = f"""
#     You are a technical interviewer. 
#     Question: "{question_text}"
#     Candidate Answer: "{candidate_answer}"
    
#     Evaluate the answer and return strictly JSON:
#     {{
#         "score": (Integer 0-100),
#         "feedback": "Constructive feedback explaining what was right/wrong (max 2 sentences)",
#         "is_correct": (Boolean)
#     }}
#     """
    
#     res = query_llm(prompt, json_mode=True)
#     try:
#         return json.loads(res)
#     except:
#         return {"score": 0, "feedback": "AI Evaluation Failed", "is_correct": False}


import json
import re
from .llm_engine import query_llm

def clean_json_string(text):
    """
    Helper to clean markdown formatting from JSON strings.
    Gemini often returns ```json ... ``` blocks.
    """
    if not text:
        return ""
    
    # Remove markdown code blocks
    cleaned = text.replace("```json", "").replace("```", "").strip()
    
    # Sometimes there might be extra text before/after the JSON array/object
    # We try to find the first '[' or '{' and the last ']' or '}'
    try:
        start_idx = cleaned.find('[')
        end_idx = cleaned.rfind(']') + 1
        if start_idx != -1 and end_idx != -1:
            return cleaned[start_idx:end_idx]
            
        start_idx = cleaned.find('{')
        end_idx = cleaned.rfind('}') + 1
        if start_idx != -1 and end_idx != -1:
            return cleaned[start_idx:end_idx]
    except:
        pass
        
    return cleaned

def generate_ai_questions(skills, job_role, experience_level):
    """
    Generates 5 technical interview questions based on skills and role.
    """
    prompt = f"""
    You are a Technical Interviewer. Generate 5 distinct technical interview questions for a {job_role} role.
    
    Candidate Skills: {', '.join(skills)}
    Experience Level: {experience_level} years
    
    Return the response as a valid JSON list of objects. Each object must have:
    - "text": The question text
    - "difficulty": "Easy", "Medium", or "Hard"
    - "topic": The specific skill or concept (e.g., "React Hooks", "Database Indexing")
    
    Example Output Format:
    [
        {{"text": "Explain the virtual DOM.", "difficulty": "Easy", "topic": "React"}},
        {{"text": "How do you handle race conditions?", "difficulty": "Hard", "topic": "Concurrency"}}
    ]
    
    Return ONLY the raw JSON. No markdown formatting.
    """
    
    # FIX: removed json_mode argument
    response_text = query_llm(prompt)
    
    clean_text = clean_json_string(response_text)
    
    try:
        return json.loads(clean_text)
    except json.JSONDecodeError:
        print(f"Error parsing AI questions JSON. Raw text: {response_text}")
        # Fallback questions if parsing fails
        return [
            {"text": "Could you describe a challenging project you worked on?", "difficulty": "Medium", "topic": "General"},
            {"text": "What are your strengths and weaknesses?", "difficulty": "Easy", "topic": "Behavioral"}
        ]

def evaluate_answer(question, answer):
    """
    Grades a candidate's answer.
    """
    prompt = f"""
    You are an expert interviewer. Grade the following answer.
    
    Question: "{question}"
    Candidate Answer: "{answer}"
    
    Return a valid JSON object with:
    - "score": Integer (0-100)
    - "feedback": A brief helpful comment (max 2 sentences)
    - "is_correct": Boolean (true/false)
    
    Return ONLY the raw JSON.
    """
    
    # FIX: removed json_mode argument
    response_text = query_llm(prompt)
    clean_text = clean_json_string(response_text)
    
    try:
        return json.loads(clean_text)
    except json.JSONDecodeError:
        return {"score": 0, "feedback": "AI Evaluation Failed to parse response.", "is_correct": False}