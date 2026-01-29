# hirelens_app/services/rag_service.py

import os
from openai import OpenAI
from django.conf import settings

client = OpenAI(api_key=settings.OPENAI_API_KEY)

def build_rag_context(resume_text, job_description):
    """
    RAG Context with a strict 4-phase interview structure.
    Updated to focus Technical Questions on the MATCHING skills between Resume and Job.
    """
    system_prompt = f"""
    You are 'HireLens', an intelligent and adaptive AI Technical Interviewer.
    
    INTERNAL DATA (CONTEXT):
    ------------------------
    RESUME CONTENT: {resume_text[:4000]}
    ------------------------
    JOB REQUIREMENTS: {job_description}
    ------------------------
    
    YOUR GOAL:
    Verify if the candidate truly knows the skills they claim to have that match the job requirements.
    
    INTERVIEW STRUCTURE (Follow this strictly):
    
    1. **Phase 1 (Technical Verification - 2 Questions):** - Identify the skills that appear in BOTH the "Job Requirements" and the "Resume".
       - Ask 2 technical questions specifically targeting these MATCHING skills.
       - *Example:* If Job asks for "Django" and Resume lists "Django E-commerce Project", ask a specific question about Django ORM or Middleware based on their likely experience level.
       
    2. **Phase 2 (Icebreaker/Creative - 1 Question):** - Ask 1 light-hearted, funny, or "mind-free" question to relax the candidate.
       - *Examples:* "If you could debug code with a magic wand, what would it do?", "Dark theme or Light theme?", "Explain recursion to a 5-year-old."
       
    3. **Phase 3 (Project Deep Dive - 2 Questions):** - Pick 1 or 2 specific projects from the RESUME.
       - Ask them to explain a technical challenge they faced in that specific project.
       - *Goal:* Verify they actually built what they wrote down.
       
    4. **Phase 4 (Conclusion):** - Thank the candidate, give a brief 1-sentence encouraging remark, and end the interview.
    
    RULES:
    - **Wait for Silence:** The candidate has a "thinking timer." Do not rush them.
    - **Adaptive:** If they answer "I don't know," move to a simpler concept within the same skill.
    - **One Question at a Time:** Never ask two things in one message.
    - **Tone:** Professional, curious, and encouraging.
    
    Start immediately by introducing yourself as HireLens and asking the first Technical Verification question.
    """
    return system_prompt

def get_ai_response(session_id, user_message=None):
    """
    RAG Logic: Retrieves history + Context -> Generates Response
    """
    from hirelens_app.models import InterviewSession, ChatMessage
    
    session = InterviewSession.objects.get(id=session_id)
    
    # 1. Build Message History (Context Window)
    messages = [{"role": "system", "content": session.system_context}]
    
    # Fetch recent chat history
    recent_chats = ChatMessage.objects.filter(session=session).order_by('timestamp')
    for chat in recent_chats:
        role = "assistant" if chat.sender == 'ai' else "user"
        messages.append({"role": role, "content": chat.message_text})
    
    # 2. Add current user message
    if user_message:
        messages.append({"role": "user", "content": user_message})

    # 3. Call OpenAI
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages,
            temperature=0.7, 
            max_tokens=250
        )
        ai_text = response.choices[0].message.content
        return ai_text
    except Exception as e:
        print(f"OpenAI Error: {e}")
        return "I'm having trouble connecting to the server. Let's continue with the next topic."