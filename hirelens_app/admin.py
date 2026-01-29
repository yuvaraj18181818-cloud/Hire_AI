from django.contrib import admin
from .models import (
    HRProfile,
    CompanyRequirement,
    Candidate,
    ResumeAnalysis,
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
# RESUME ANALYSIS
# -----------------------------
@admin.register(ResumeAnalysis)
class ResumeAnalysisAdmin(admin.ModelAdmin):
    list_display = (
        "candidate",
        "job",
        "similarity_score",
        "short_summary", # Custom method below
        "analysis_time"
    )
    list_filter = ("job",)
    search_fields = ("candidate__name",)
    
    def short_summary(self, obj):
        return obj.ai_summary[:50] + "..." if obj.ai_summary else "-"
    short_summary.short_description = "AI Summary Preview"

# -----------------------------
# NEW: AI GENERATED QUESTIONS
# -----------------------------
@admin.register(GeneratedQuestion)
class GeneratedQuestionAdmin(admin.ModelAdmin):
    list_display = ("analysis", "topic", "difficulty", "short_question")
    list_filter = ("difficulty", "topic")
    search_fields = ("question_text", "topic")

    def short_question(self, obj):
        return obj.question_text[:50] + "..."
    short_question.short_description = "Question"

# -----------------------------
# INTERVIEW RESULTS (Updated)
# -----------------------------
@admin.register(InterviewResult)
class InterviewResultAdmin(admin.ModelAdmin):
    # Updated to reflect new fields (question link, ai_score, etc.)
    list_display = ("get_candidate", "get_question_topic", "ai_score", "is_correct", "submitted_at")
    list_filter = ("is_correct", "ai_score")
    
    def get_candidate(self, obj):
        return obj.question.analysis.candidate.name
    get_candidate.short_description = "Candidate"
    
    def get_question_topic(self, obj):
        return obj.question.topic
    get_question_topic.short_description = "Topic"

# -----------------------------
# COURSE RECOMMENDATIONS
# -----------------------------
@admin.register(CourseRecommendation)
class CourseRecommendationAdmin(admin.ModelAdmin):
    list_display = ("analysis", "skill_name", "course_name")
    search_fields = ("skill_name", "course_name")