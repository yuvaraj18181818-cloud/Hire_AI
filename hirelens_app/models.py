from django.db import models
from django.contrib.auth.models import User

# =================================================
# HR PROFILE
# =================================================
class HRProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    company_name = models.CharField(max_length=150)

    def __str__(self):
        return f"{self.user.username} ({self.company_name})"


# =================================================
# COMPANY JOB REQUIREMENTS (HR INPUT)
# =================================================
class CompanyRequirement(models.Model):
    hr = models.ForeignKey(HRProfile, on_delete=models.CASCADE)
    job_title = models.CharField(max_length=150)
    required_skills = models.TextField(
        help_text="Comma-separated skills (e.g., python, django, communication)"
    )
    minimum_experience = models.IntegerField(help_text="Years of experience")
    created_at = models.DateTimeField(auto_now_add=True)

    def skill_list(self):
        return [s.strip().lower() for s in self.required_skills.split(",")]

    def __str__(self):
        return f"{self.job_title} - {self.hr.company_name}"


# =================================================
# CANDIDATE PROFILE
# =================================================
class Candidate(models.Model):
    name = models.CharField(max_length=120)
    email = models.EmailField()
    phone = models.CharField(max_length=20)
    resume = models.FileField(upload_to="resumes/")
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


# =================================================
# RESUME ANALYSIS (Updated for AI & Interview Results)
# =================================================
class ResumeAnalysis(models.Model):
    candidate = models.ForeignKey(Candidate, on_delete=models.CASCADE)
    job = models.ForeignKey(CompanyRequirement, on_delete=models.CASCADE)
    
    # 1. Resume Screening Results
    similarity_score = models.FloatField(default=0.0)
    ai_summary = models.TextField(blank=True, default="Pending Analysis...")
    extracted_skills_list = models.TextField(blank=True, default="", help_text="Comma-separated list of extracted skills")
    
    # 🔥 2. NEW: Interview Results (Added for End Session)
    interview_score = models.IntegerField(default=0, help_text="Overall AI Interview Score (0-100)")
    interview_feedback = models.TextField(blank=True, default="", help_text="AI feedback summary")
    detailed_breakdown = models.JSONField(default=list, blank=True, help_text="JSON list of topic-wise scores")
    
    analysis_time = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.candidate.name} → {self.job.job_title}"


# =================================================
# INTERVIEW SESSION (Tracks the Chat)
# =================================================
class InterviewSession(models.Model):
    analysis = models.ForeignKey(ResumeAnalysis, on_delete=models.CASCADE)
    start_time = models.DateTimeField(auto_now_add=True)
    is_completed = models.BooleanField(default=False)
    
    # RAG Context: We store the 'System Prompt' here to ensure consistency
    system_context = models.TextField(blank=True)

    def __str__(self):
        return f"Session: {self.analysis.candidate.name}"


# =================================================
# CHAT MESSAGE (Stores Transcript)
# =================================================
class ChatMessage(models.Model):
    session = models.ForeignKey(InterviewSession, on_delete=models.CASCADE)
    sender = models.CharField(max_length=10) # 'ai' or 'candidate'
    message_text = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.sender}: {self.message_text[:30]}..."


# =================================================
# LEGACY / EXTRA MODELS (Optional)
# =================================================
# You can keep these if you still use them for other features, 
# but the new RAG Interview system mainly uses the models above.

class GeneratedQuestion(models.Model):
    analysis = models.ForeignKey(ResumeAnalysis, on_delete=models.CASCADE)
    question_text = models.TextField()
    difficulty = models.CharField(max_length=50)
    topic = models.CharField(max_length=100)
    
    def __str__(self):
        return f"{self.topic}: {self.question_text[:30]}..."

class InterviewResult(models.Model):
    question = models.ForeignKey(GeneratedQuestion, on_delete=models.CASCADE, null=True, blank=True)
    candidate_answer = models.TextField(blank=True, default="")
    ai_score = models.IntegerField(default=0)
    ai_feedback = models.TextField(default="No feedback provided.")
    is_correct = models.BooleanField(default=False)
    submitted_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Answer to {self.question.id} (Score: {self.ai_score})"

class CourseRecommendation(models.Model):
    analysis = models.ForeignKey(ResumeAnalysis, on_delete=models.CASCADE)
    skill_name = models.CharField(max_length=100)
    course_name = models.CharField(max_length=200)
    course_link = models.URLField()

    def __str__(self):
        return f"{self.skill_name} → {self.course_name}"