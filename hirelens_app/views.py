from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, JsonResponse
from django.views.decorators.http import require_POST
import json

# Import Models
from .models import (
    HRProfile,
    CompanyRequirement,
    Candidate,
    ResumeAnalysis,
    GeneratedQuestion,
    InterviewResult,
    CourseRecommendation
)

# Import AI Services
from .services.resume_parser import parse_resume_smart
from .services.interview_engine import generate_ai_questions, evaluate_answer
from .services.course_recommender import recommend_courses_smart

# =================================================
# HR DASHBOARD
# =================================================
# hirelens_app/views.py

from django.db.models import Count, Avg

@login_required
def hr_dashboard(request):
    """
    HR Dashboard view that displays company information, job statistics,
    and detailed job listings with candidate analytics.
    """
    # Get or create HR profile for the logged-in user
    hr, _ = HRProfile.objects.get_or_create(
        user=request.user,
        defaults={"company_name": "Default Company"}
    )
    
    # Annotate jobs with candidate count and average similarity score
    jobs = CompanyRequirement.objects.filter(hr=hr).annotate(
        candidate_count=Count('resumeanalysis__candidate', distinct=True),
        avg_score=Avg('resumeanalysis__similarity_score')
    ).order_by('-created_at')
    
    # Calculate total number of candidates across all jobs
    total_candidates = ResumeAnalysis.objects.filter(
        job__hr=hr
    ).values('candidate').distinct().count()
    
    # Calculate total number of scheduled interviews
    total_interviews = InterviewResult.objects.filter(
        question__analysis__job__hr=hr
    ).count()

    context = {
        "jobs": jobs,
        "total_candidates": total_candidates,
        "total_interviews": total_interviews,
    }
    
    return render(request, "hirelens_app/hr_dashboard.html", context)


@login_required
def view_candidates(request, job_id):
    """
    View all candidates who applied for a specific job with their analysis results.
    """
    # Get the job and ensure it belongs to the logged-in HR
    job = get_object_or_404(CompanyRequirement, id=job_id, hr__user=request.user)
    
    # Get all resume analyses for this job with related candidate data
    analyses = ResumeAnalysis.objects.filter(job=job).select_related(
        'candidate'
    ).annotate(
        questions_count=Count('generatedquestion', distinct=True),
        interviews_count=Count('generatedquestion__interviewresult', distinct=True)
    ).order_by('-similarity_score', '-analysis_time')
    
    # Process extracted skills for each analysis
    for analysis in analyses:
        if analysis.extracted_skills_list:
            analysis.skills_list = [skill.strip() for skill in analysis.extracted_skills_list.split(',')]
        else:
            analysis.skills_list = []
    
    # Calculate statistics
    total_applicants = analyses.count()
    avg_score = analyses.aggregate(Avg('similarity_score'))['similarity_score__avg'] or 0
    high_match_count = analyses.filter(similarity_score__gte=70).count()
    medium_match_count = analyses.filter(
        similarity_score__gte=40, 
        similarity_score__lt=70
    ).count()
    low_match_count = analyses.filter(similarity_score__lt=40).count()
    
    # Process required skills for the job
    required_skills_list = [skill.strip() for skill in job.required_skills.split(',')]
    
    context = {
        'job': job,
        'analyses': analyses,
        'total_applicants': total_applicants,
        'avg_score': round(avg_score, 2),
        'high_match_count': high_match_count,
        'medium_match_count': medium_match_count,
        'low_match_count': low_match_count,
        'required_skills_list': required_skills_list,
    }
    
    return render(request, 'hirelens_app/view_candidates.html', context)

@login_required
def hr_dashboard_with_error_handling(request):
    """
    HR Dashboard view with comprehensive error handling.
    """
    try:
        # Get or create HR profile
        hr, created = HRProfile.objects.get_or_create(
            user=request.user,
            defaults={"company_name": "Default Company"}
        )
        
        # Fetch jobs with annotations
        jobs = CompanyRequirement.objects.filter(hr=hr).annotate(
            candidate_count=Count('resumeanalysis__candidate', distinct=True),
            avg_score=Avg('resumeanalysis__similarity_score')
        ).order_by('-created_at')
        
        # Calculate statistics
        total_candidates = sum(job.candidate_count or 0 for job in jobs)
        
        total_interviews = InterviewResult.objects.filter(
            question__analysis__job__hr=hr
        ).count()
        
        context = {
            "jobs": jobs,
            "total_candidates": total_candidates,
            "total_interviews": total_interviews,
            "hr_profile": hr,
        }
        
        return render(request, "hirelens_app/hr_dashboard.html", context)
        
    except Exception as e:
        # Log the error (you should configure proper logging)
        print(f"Error in hr_dashboard: {str(e)}")
        
        # Return a safe fallback
        context = {
            "jobs": CompanyRequirement.objects.none(),
            "total_candidates": 0,
            "total_interviews": 0,
            "error_message": "Unable to load dashboard data. Please try again.",
        }
        return render(request, "hirelens_app/hr_dashboard.html", context)

# =================================================
# ADD COMPANY JOB REQUIREMENT
# =================================================
@login_required
def job_requirement(request):
    hr, _ = HRProfile.objects.get_or_create(user=request.user)

    if request.method == "POST":
        CompanyRequirement.objects.create(
            hr=hr,
            job_title=request.POST.get("job_title"),
            required_skills=request.POST.get("skills"),
            minimum_experience=request.POST.get("experience")
        )
        return redirect("hr_dashboard")

    return render(request, "hirelens_app/job_requirement.html")


# =================================================
# UPLOAD RESUME
# =================================================
@login_required
def upload_resume(request):
    hr = get_object_or_404(HRProfile, user=request.user)
    jobs = CompanyRequirement.objects.filter(hr=hr)

    if request.method == "POST":
        job_id = request.POST.get("job")

        if not job_id:
            return render(request, "hirelens_app/upload_resume.html", {
                "jobs": jobs,
                "error": "Please select a job requirement."
            })

        # Save Candidate
        candidate = Candidate.objects.create(
            name=request.POST.get("name"),
            email=request.POST.get("email"),
            phone=request.POST.get("phone"),
            resume=request.FILES.get("resume")
        )

        # Redirect to Analysis Pipeline
        return redirect("analyze_resume", candidate.id, job_id)

    return render(request, "hirelens_app/upload_resume.html", {
        "jobs": jobs
    })


# =================================================
# RESUME ANALYSIS PIPELINE (AI Powered)
# =================================================
@login_required
def analyze_resume(request, candidate_id, job_id):
    candidate = get_object_or_404(Candidate, id=candidate_id)
    job = get_object_or_404(CompanyRequirement, id=job_id)

    # 1. AI Parse Resume
    parsed_data = parse_resume_smart(candidate.resume.path)
    extracted_skills = parsed_data.get("skills", [])
    
    # Clean list: remove empty strings and lower case
    extracted_skills = [s.strip() for s in extracted_skills if s.strip()]
    
    ai_summary = parsed_data.get("summary", "Analysis pending...")
    candidate_experience = parsed_data.get("experience_years", 0)

    # 2. Strict Matching Logic
    req_skills_list = [s.strip().lower() for s in job.required_skills.split(",") if s.strip()]
    cand_skills_lower = [s.lower() for s in extracted_skills]
    
    matched_skills = set()
    for req in req_skills_list:
        # Strict Check: Requirement must explicitly exist or be a clear parent
        # e.g. "react" matches "reactjs" or "react.js", but "java" does NOT match "javascript"
        for cand in cand_skills_lower:
            if req == cand: # Exact match
                matched_skills.add(req)
            elif req in cand and len(cand) < len(req) + 4: # Allow "react" -> "reactjs"
                matched_skills.add(req)
            elif f" {req} " in f" {cand} ": # Word boundary match "core java" -> "java"
                matched_skills.add(req)

    missing_skills = set(req_skills_list).difference(matched_skills)
    
    score = (len(matched_skills) / len(req_skills_list)) * 100 if req_skills_list else 0

    # 3. Save Analysis Result
    analysis = ResumeAnalysis.objects.create(
        candidate=candidate,
        job=job,
        similarity_score=round(score, 1),
        ai_summary=ai_summary,
        extracted_skills_list=",".join(extracted_skills) 
    )

    # 4. Generate AI Questions & Courses (Keep existing logic)
    questions = generate_ai_questions(extracted_skills, job.job_title, candidate_experience)
    for q in questions:
        GeneratedQuestion.objects.create(
            analysis=analysis,
            question_text=q.get("text", "Default Question"),
            difficulty=q.get("difficulty", "Medium"),
            topic=q.get("topic", "General")
        )

    recs = recommend_courses_smart(list(missing_skills))
    for r in recs:
        CourseRecommendation.objects.create(
            analysis=analysis,
            skill_name=r["skill"],
            course_name=r["course"],
            course_link=r["link"]
        )

    return redirect("analysis_result", analysis.id)
# =================================================
# ANALYSIS RESULT VIEW
# =================================================
# hirelens_app/views.py

@login_required
def analysis_result(request, analysis_id):
    analysis = get_object_or_404(ResumeAnalysis, id=analysis_id)
    courses = CourseRecommendation.objects.filter(analysis=analysis)
    
    # ---------------------------------------------------------
    # 🔥 FIXED VISUALIZATION LOGIC
    # ---------------------------------------------------------
    job_reqs = [s.strip() for s in analysis.job.required_skills.split(",") if s.strip()]
    
    # Get CLEAN list from DB
    if analysis.extracted_skills_list:
        found_skills_clean = [s.strip().lower() for s in analysis.extracted_skills_list.split(",")]
    else:
        found_skills_clean = []

    skills_data = []
    for req_skill in job_reqs:
        req_lower = req_skill.lower()
        is_present = False
        
        # Apply SAME Strict Matching Logic here for display
        for found in found_skills_clean:
            if req_lower == found:
                is_present = True; break
            if req_lower in found and len(found) < len(req_lower) + 4:
                is_present = True; break
            if f" {req_lower} " in f" {found} ":
                is_present = True; break
        
        skills_data.append({
            "skill_name": req_skill,
            "is_present": is_present,
            # Explicit float value for template math
            "similarity_score": 0.95 if is_present else 0.10 
        })

    return render(request, "hirelens_app/analysis_result.html", {
        "analysis": analysis,
        "courses": courses,
        "skills": skills_data,
        "summary": analysis.ai_summary
    })
# =================================================
# INTERVIEW PAGE
# =================================================
# hirelens_app/views.py

@login_required
def interview(request, analysis_id):
    """
    Redirects the old 'Start Interview' link to the new RAG Session Starter.
    This ensures the session is created and the AI context is built before loading the chat.
    """
    return redirect('start_interview_session', analysis_id=analysis_id)


# =================================================
# SUBMIT INTERVIEW ANSWER (AI Grading)
# =================================================
@require_POST
@login_required
def submit_interview_answer(request):
    question_id = request.POST.get("question_id")
    answer_text = request.POST.get("answer")
    
    if not question_id or not answer_text:
        return HttpResponse("Missing Data", status=400)
        
    question = get_object_or_404(GeneratedQuestion, id=question_id)
    
    # 1. AI Evaluates the Answer
    evaluation = evaluate_answer(question.question_text, answer_text)
    
    # 2. Save the Result
    InterviewResult.objects.create(
        question=question,
        candidate_answer=answer_text,
        ai_score=evaluation.get("score", 0),
        ai_feedback=evaluation.get("feedback", "No feedback generated."),
        is_correct=evaluation.get("is_correct", False)
    )
    
    # 3. Redirect back to the interview page to see the score
    return redirect("interview_bot", analysis_id=question.analysis.id)

# =================================================
# IMPROVEMENT PLAN (Simple Redirect to Analysis for now)
# =================================================
@login_required
def improvement_plan(request, analysis_id):
    # Since we now show recommendations directly on the result page, 
    # we can redirect there or render a specific print-friendly view.
    return redirect("analysis_result", analysis_id=analysis_id)


# hirelens_app/views.py

from django.http import JsonResponse
from .models import InterviewSession, ChatMessage
from .services.rag_service import build_rag_context, get_ai_response
import json

# ... (Keep your existing Dashboard/Upload views) ...

# =================================================
# 1. START INTERVIEW SESSION
# =================================================
@login_required
def start_interview_session(request, analysis_id):
    analysis = get_object_or_404(ResumeAnalysis, id=analysis_id)
    
    # 1. Build the RAG Context (Internal Data)
    # We load the full resume text again (or you can save it in the model)
    from .services.resume_parser import extract_text_from_file
    resume_text = extract_text_from_file(analysis.candidate.resume.path)
    
    system_context = build_rag_context(resume_text, analysis.job.required_skills)
    
    # 2. Create Session
    session = InterviewSession.objects.create(
        analysis=analysis,
        system_context=system_context
    )
    
    # 3. Generate Opening Message (The "Hello")
    initial_greeting = get_ai_response(session.id, user_message="Start the interview now.")
    
    ChatMessage.objects.create(session=session, sender='ai', message_text=initial_greeting)
    
    # Redirect to the Chat Interface
    return redirect('interview_bot', session_id=session.id)

# =================================================
# 2. RENDER CHAT INTERFACE
# =================================================
@login_required
def interview_bot(request, session_id):
    session = get_object_or_404(InterviewSession, id=session_id)
    return render(request, "hirelens_app/interview_bot.html", {"session": session})

# =================================================
# 3. API: SEND MESSAGE & GET AI RESPONSE
# =================================================
@require_POST
def api_chat_interaction(request):
    try:
        data = json.loads(request.body)
        session_id = data.get('session_id')
        user_text = data.get('message')
        
        session = InterviewSession.objects.get(id=session_id)
        
        # 1. Save Candidate Message
        ChatMessage.objects.create(session=session, sender='candidate', message_text=user_text)
        
        # 2. Get AI Response (RAG)
        ai_text = get_ai_response(session_id, user_text)
        
        # 3. Save AI Message
        ChatMessage.objects.create(session=session, sender='ai', message_text=ai_text)
        
        return JsonResponse({'status': 'success', 'ai_response': ai_text})
        
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)