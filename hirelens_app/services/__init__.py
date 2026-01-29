# hirelens_app/services/__init__.py
# mark as package; keep lightweight to avoid import-time heavy deps

__all__ = [
    "embedding",
    "resume_parser",
    "requirements_engine",
    "similarity_engine",
    "skill_engine",
    "evaluation_engine",
    "course_engine",
    "improvement_plan",
    "interview_engine",
]
