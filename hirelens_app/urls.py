from django.urls import path
from . import views

urlpatterns = [

    # -------------------------------
    # HR DASHBOARD & REQUIREMENTS
    # -------------------------------
    path("", views.hr_dashboard, name="hr_dashboard"),

    path("job-requirement/", 
         views.job_requirement, 
         name="job_requirement"),

    # -------------------------------
    # CANDIDATES VIEW
    # -------------------------------
    path("job/<int:job_id>/candidates/", 
         views.view_candidates, 
         name="view_candidates"),

    # -------------------------------
    # RESUME UPLOAD & ANALYSIS PIPELINE
    # -------------------------------
    path("upload-resume/", 
         views.upload_resume, 
         name="upload_resume"),

    # Triggers the AI Analysis (Resume Parse + Question Generation)
    path("analyze/<int:candidate_id>/<int:job_id>/", 
         views.analyze_resume, 
         name="analyze_resume"),

    # Shows the results (Similarity Score, AI Summary, Recommendations)
    path("analysis-result/<int:analysis_id>/", 
         views.analysis_result, 
         name="analysis_result"),

    # -------------------------------
    # INTERVIEW FLOW (AI Powered)
    # -------------------------------
    # Displays the AI-generated questions for this specific candidate
    path("interview/<int:analysis_id>/", 
         views.interview, 
         name="interview"),

    # Endpoint to submit an answer for AI grading (POST request)
    path("interview/submit/", 
         views.submit_interview_answer, 
         name="submit_interview_answer"),

    # -------------------------------
    # LEGACY / REDIRECTS
    # -------------------------------
    # Kept for backward compatibility; now redirects to analysis_result
    path("improvement-plan/<int:analysis_id>/", 
         views.improvement_plan, 
         name="improvement_plan"),

     path('interview/start/<int:analysis_id>/', views.start_interview_session, name='start_interview_session'),
     path('interview/bot/<int:session_id>/', views.interview_bot, name='interview_bot'),
     path('api/chat/', views.api_chat_interaction, name='api_chat_interaction'),
]