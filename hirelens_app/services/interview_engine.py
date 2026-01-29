import json
from .llm_engine import query_llm

def generate_ai_questions(skills, job_role, experience_level):
    """Generates 5 unique interview questions based on candidate skills"""
    
    prompt = f"""
    Generate 5 technical interview questions for a '{job_role}' position.
    Candidate Skills: {', '.join(skills)}.
    Experience Level: {experience_level} years.
    
    Output strictly a JSON array:
    {{
        "questions": [
            {{ "text": "Question 1", "difficulty": "Medium", "topic": "SkillName" }},
            {{ "text": "Question 2", "difficulty": "Hard", "topic": "SkillName" }}
        ]
    }}
    """
    
    res = query_llm(prompt, json_mode=True)
    try:
        data = json.loads(res)
        return data.get("questions", [])
    except:
        return []

def evaluate_answer(question_text, candidate_answer):
    """Grades the answer"""
    
    prompt = f"""
    You are a technical interviewer. 
    Question: "{question_text}"
    Candidate Answer: "{candidate_answer}"
    
    Evaluate the answer and return strictly JSON:
    {{
        "score": (Integer 0-100),
        "feedback": "Constructive feedback explaining what was right/wrong (max 2 sentences)",
        "is_correct": (Boolean)
    }}
    """
    
    res = query_llm(prompt, json_mode=True)
    try:
        return json.loads(res)
    except:
        return {"score": 0, "feedback": "AI Evaluation Failed", "is_correct": False}