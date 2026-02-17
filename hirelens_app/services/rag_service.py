import google.generativeai as genai
from django.conf import settings
import json
import re

# Configure Gemini
try:
    genai.configure(api_key=settings.GEMINI_API_KEY)
except AttributeError:
    print("WARNING: GEMINI_API_KEY not found in settings.")

# Helper to clean JSON
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

# ==========================================
# 1. BUILD CONTEXT (Fixes ImportError)
# ==========================================
# hirelens_app/services/rag_service.py

def build_rag_context(resume_text, job_description):
    """
    Constructs the System Instruction for Gemini.
    """
    system_prompt = f"""
    You are 'HireLens', a friendly, energetic, and slightly witty AI Technical Interviewer.
    
    CONTEXT:
    RESUME: {resume_text[:15000]} 
    JOB: {job_description}
    
    YOUR GOAL:
    Conduct a structured interview following an EXACT sequence. You must track which phase you are in.
    
    ══════════════════════════════════════
    INTERVIEW FLOW (Follow this EXACTLY):
    ══════════════════════════════════════
    
    PHASE 1 — GREETING + QUESTION 1:
    Introduce yourself briefly (1 sentence). Then ask the FIRST simple technical question based on the candidate's skills from the resume. Keep it basic and foundational.
    
    PHASE 2 — QUESTION 2:
    After the candidate answers Q1, give brief feedback (1 sentence) and ask the SECOND technical question. Slightly harder than Q1, still based on their resume skills.
    
    PHASE 3 — JOKE + QUESTION 3:
    After Q2 is answered, first make a SHORT, FUNNY JOKE or witty comment based on the candidate's previous answers (1-2 sentences). Then ask the THIRD and final technical question. This should be moderately challenging.
    
    PHASE 4 — PROJECT QUESTION:
    After Q3 is answered, give brief feedback. Then ask ONE high-value question specifically about a PROJECT mentioned in the candidate's resume. Ask about their role, challenges faced, or a specific technical decision they made. This is the most important question.
    
    PHASE 5 — TRICKY FUN QUESTION:
    After the project answer, ask ONE tricky, funny, real-world scenario question. Example style: "If your production server crashed at 3 AM on a Friday and you had a pizza in the oven, what would you do first?" — Make it relevant to their tech stack but humorous.
    
    PHASE 6 — END:
    After they answer the tricky question, thank them warmly, give a brief overall impression (2 sentences), and say goodbye. End with EXACTLY this marker on its own line: [INTERVIEW_COMPLETE]
    
    ══════════════════════════════════════
    CRITICAL RULES:
    ══════════════════════════════════════
    1. **KEEP IT SHORT**: Your responses must be 1-3 sentences MAX (except the joke phase where you can add the joke + question).
    2. **ONE QUESTION AT A TIME**: Never ask more than one question per message.
    3. **FOLLOW THE PHASES IN ORDER**: Do NOT skip phases. Do NOT add extra questions.
    4. **TOTAL QUESTIONS = 5**: Exactly 3 technical + 1 project + 1 tricky fun = 5 questions total.
    5. **USE EMOJIS SPARINGLY**: One emoji per message max. Keep it professional but warm.
    6. **WHEN DONE**: You MUST include [INTERVIEW_COMPLETE] at the end of your final goodbye message in Phase 6.
    
    Start with Phase 1 now.
    """
    return system_prompt

# ==========================================
# 2. CHAT BOT RESPONSE
# ==========================================
import time as _time

def get_ai_response(session_id, user_message=None):
    """
    Generates the AI's reply during the interview.
    Tracks the interview phase based on AI question count in chat history.
    """
    # Import inside function to prevent Circular Import Error
    from hirelens_app.models import InterviewSession, ChatMessage
    
    try:
        session = InterviewSession.objects.get(id=session_id)
        
        # Auto-Fallback Models (updated to current Gemini model names)
        models_to_try = ['gemini-2.5-flash-preview-09-2025', 'gemini-3-flash-preview', 'gemini-1.5-pro']
        
        # Prepare History
        history = [
            {"role": "user", "parts": [session.system_context]},
            {"role": "model", "parts": ["Understood. I will follow the exact 6-phase interview flow."]}
        ]
        
        recent_chats = ChatMessage.objects.filter(session=session).order_by('timestamp')
        
        # Count how many AI messages exist (to determine current phase)
        ai_message_count = 0
        for chat in recent_chats:
            role = "model" if chat.sender == 'ai' else "user"
            msg = chat.message_text if chat.message_text else "..."
            history.append({"role": role, "parts": [msg]})
            if chat.sender == 'ai':
                ai_message_count += 1
        
        # Determine phase reminder based on AI message count
        # AI msg 0 = about to send greeting+Q1 (Phase 1)
        # AI msg 1 = already sent Q1, now send Q2 (Phase 2)
        # AI msg 2 = already sent Q2, now joke+Q3 (Phase 3)
        # AI msg 3 = already sent Q3, now project Q (Phase 4)
        # AI msg 4 = already sent project Q, now tricky fun Q (Phase 5)
        # AI msg 5 = already sent tricky Q, now say goodbye (Phase 6)
        phase_reminders = {
            0: "You are in PHASE 1: Greet briefly and ask the first simple technical question.",
            1: "You are in PHASE 2: Give brief feedback on their answer, then ask the second technical question (slightly harder).",
            2: "You are in PHASE 3: Make a SHORT funny joke based on their previous answers, then ask the third technical question.",
            3: "You are in PHASE 4: Give brief feedback, then ask ONE high-value question about a specific PROJECT from their resume.",
            4: "You are in PHASE 5: Ask ONE tricky, funny, real-world scenario question related to their tech stack. Make it humorous!",
            5: "You are in PHASE 6: Thank them warmly, give a 2-sentence overall impression, say goodbye, and end with [INTERVIEW_COMPLETE] on its own line.",
        }
        
        phase_hint = phase_reminders.get(ai_message_count, 
            "The interview is complete. Say goodbye warmly and include [INTERVIEW_COMPLETE] on its own line.")
            
        msg_to_send = user_message if user_message else "Hello, let's start the interview."
        
        # Append phase instruction to the user message
        if ai_message_count > 0:
            msg_to_send = f"{msg_to_send}\n\n[SYSTEM REMINDER: {phase_hint}]"
        else:
            msg_to_send = f"{msg_to_send}\n\n[SYSTEM REMINDER: {phase_hint}]"

        last_error = None
        for model_name in models_to_try:
            # Retry with backoff for rate limit errors
            for attempt in range(3):
                try:
                    model = genai.GenerativeModel(model_name)
                    chat_session = model.start_chat(history=history)
                    response = chat_session.send_message(msg_to_send)
                    response_text = response.text.strip()
                    
                    # Clean the [SYSTEM REMINDER] tags from response if AI echoes them
                    response_text = re.sub(r'\[SYSTEM REMINDER:.*?\]', '', response_text).strip()
                    
                    return response_text
                except Exception as e:
                    last_error = e
                    error_str = str(e)
                    print(f"[HireLens] Model '{model_name}' attempt {attempt+1} failed: {error_str}")
                    
                    # If rate-limited (429), wait and retry
                    if '429' in error_str or 'ResourceExhausted' in error_str or 'quota' in error_str.lower():
                        wait_time = (attempt + 1) * 5  # 5s, 10s, 15s
                        print(f"[HireLens] Rate limited. Waiting {wait_time}s before retry...")
                        _time.sleep(wait_time)
                        continue
                    else:
                        break  # Non-rate-limit error, try next model
        
        # All models failed — return descriptive message
        error_msg = str(last_error) if last_error else 'Unknown error'
        if '429' in error_msg or 'quota' in error_msg.lower():
            print(f"[HireLens] QUOTA EXHAUSTED: {error_msg}")
            return "I'm experiencing high demand. The AI quota has been temporarily exceeded. Please wait a minute and try again, or contact your administrator to upgrade the API plan."
        
        print(f"[HireLens] ALL MODELS FAILED. Last error: {error_msg}")
        return f"I encountered a technical issue. Please try again. (Error: {error_msg[:100]})"
        
    except Exception as e:
        print(f"[HireLens] System Error: {e}")
        return f"Connection error: {str(e)[:100]}"

# ==========================================
# 3. GENERATE FINAL FEEDBACK (For End Session)
# ==========================================
def generate_interview_feedback(session, chat_history):
    """
    Analyzes the full interview transcript and returns scores/feedback.
    """
    # 1. Format history for the prompt
    transcript = ""
    for msg in chat_history:
        sender = "AI Interviewer" if msg.sender == 'ai' else "Candidate"
        transcript += f"{sender}: {msg.message_text}\n"

    # 2. Build Grading Prompt
    prompt = f"""
    You are an Expert Technical Interviewer. Grade this interview session.
    
    TRANSCRIPT:
    {transcript[:25000]}
    
    TASK:
    Provide a structured evaluation in JSON format with these exact keys:
    1. "overall_score": Integer (0-100).
    2. "overall_feedback": A summary paragraph of performance.
    3. "breakdown": A list of objects with "topic", "score" (0-10), and "feedback".
    
    Return ONLY valid JSON.
    """

    models_to_try = ['gemini-2.0-flash-lite-001', 'gemini-flash-lite-latest', 'gemini-1.5-pro']
    
    for model_name in models_to_try:
        for attempt in range(3):
            try:
                model = genai.GenerativeModel(model_name)
                response = model.generate_content(prompt)
                clean_text = clean_json_string(response.text)
                return json.loads(clean_text)
            except Exception as e:
                error_str = str(e)
                print(f"[HireLens] Grading Error ({model_name}, attempt {attempt+1}): {error_str}")
                if '429' in error_str or 'quota' in error_str.lower():
                    import time as _time
                    _time.sleep((attempt + 1) * 5)
                    continue
                else:
                    break  # Non-rate-limit error, try next model

    return {
        "overall_score": 0,
        "overall_feedback": "AI could not generate feedback. The API quota may be exhausted. Please try again later or upgrade your Gemini API plan.",
        "breakdown": []
    }