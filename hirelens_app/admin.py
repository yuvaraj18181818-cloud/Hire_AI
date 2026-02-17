from django.contrib import admin
from .models import (
    HRProfile,
    CompanyRequirement,
    Candidate,
    ResumeAnalysis,
    InterviewSession,
    ChatMessage,
    GeneratedQuestion,
    InterviewResult,
    CourseRecommendation
)

# -----------------------------
# HR & JOB CONFIG
# -----------------------------
@admin.register(HRProfile)
class HRProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "company_name")
    search_fields = ("company_name", "user__username")

@admin.register(CompanyRequirement)
class CompanyRequirementAdmin(admin.ModelAdmin):
    list_display = ("job_title", "hr", "minimum_experience", "created_at")
    search_fields = ("job_title",)
    list_filter = ("created_at",)

# -----------------------------
# CANDIDATES
# -----------------------------
@admin.register(Candidate)
class CandidateAdmin(admin.ModelAdmin):
    list_display = ("name", "email", "phone", "uploaded_at")
    search_fields = ("name", "email")

# -----------------------------
# RESUME ANALYSIS (Updated)
# -----------------------------
@admin.register(ResumeAnalysis)
class ResumeAnalysisAdmin(admin.ModelAdmin):
    list_display = (
        "candidate",
        "job",
        "similarity_score",
        "interview_score",  # 🔥 NEW FIELD
        "short_summary",
        "analysis_time"
    )
    list_filter = ("job", "similarity_score", "interview_score")
    search_fields = ("candidate__name", "job__job_title")
    
    def short_summary(self, obj):
        return obj.ai_summary[:50] + "..." if obj.ai_summary else "-"
    short_summary.short_description = "AI Summary Preview"

# -----------------------------
# NEW: INTERVIEW SESSION (Tracks Chat Context)
# -----------------------------
@admin.register(InterviewSession)
class InterviewSessionAdmin(admin.ModelAdmin):
    list_display = ("id", "get_candidate", "get_job", "start_time", "is_completed")
    list_filter = ("is_completed", "start_time")
    search_fields = ("analysis__candidate__name",)

    def get_candidate(self, obj):
        return obj.analysis.candidate.name
    get_candidate.short_description = "Candidate"

    def get_job(self, obj):
        return obj.analysis.job.job_title
    get_job.short_description = "Job Role"

# -----------------------------
# NEW: CHAT MESSAGES (Transcript)
# -----------------------------
@admin.register(ChatMessage)
class ChatMessageAdmin(admin.ModelAdmin):
    list_display = ("session", "sender", "short_message", "timestamp")
    list_filter = ("sender", "timestamp")
    search_fields = ("message_text",)

    def short_message(self, obj):
        return obj.message_text[:60] + "..."
    short_message.short_description = "Message Content"

# -----------------------------
# LEGACY / EXTRA MODELS
# -----------------------------
@admin.register(GeneratedQuestion)
class GeneratedQuestionAdmin(admin.ModelAdmin):
    list_display = ("analysis", "topic", "difficulty", "short_question")
    list_filter = ("difficulty", "topic")
    search_fields = ("question_text", "topic")

    def short_question(self, obj):
        return obj.question_text[:50] + "..."
    short_question.short_description = "Question"

@admin.register(InterviewResult)
class InterviewResultAdmin(admin.ModelAdmin):
    list_display = ("get_candidate", "ai_score", "is_correct", "submitted_at")
    list_filter = ("is_correct", "ai_score")
    
    def get_candidate(self, obj):
        if obj.question:
            return obj.question.analysis.candidate.name
        return "Unknown"
    get_candidate.short_description = "Candidate"

@admin.register(CourseRecommendation)
class CourseRecommendationAdmin(admin.ModelAdmin):
    list_display = ("analysis", "skill_name", "course_name")
    search_fields = ("skill_name", "course_name")