# A safe library of high-quality courses (AI can hallucinate bad links, so we map to these)
COURSE_LIBRARY = {
    "python": {"name": "Complete Python Bootcamp", "link": "https://udemy.com/course/complete-python-bootcamp/"},
    "django": {"name": "Django Full Stack", "link": "https://udemy.com/course/python-django-dev-to-deployment/"},
    "react": {"name": "React - The Complete Guide", "link": "https://udemy.com/course/react-the-complete-guide/"},
    "rust": {"name": "The Rust Programming Language", "link": "https://www.udemy.com/course/the-rust-programming-language/"},
    "aws": {"name": "AWS Certified Solutions Architect", "link": "https://udemy.com/course/aws-certified-solutions-architect-associate/"},
    "javascript": {"name": "JavaScript: The Weird Parts", "link": "https://udemy.com/course/understand-javascript/"},
    # Add more here...
}

def recommend_courses_smart(missing_skills):
    recommendations = []
    
    for skill in missing_skills:
        # Normalize skill name (e.g. "ReactJS" -> "react")
        clean_skill = skill.lower().strip()
        
        # Simple string matching (Safe & Production Ready)
        matched_key = None
        for key in COURSE_LIBRARY:
            if key in clean_skill or clean_skill in key:
                matched_key = key
                break
        
        if matched_key:
            data = COURSE_LIBRARY[matched_key]
            recommendations.append({
                "skill": skill,
                "course": data["name"],
                "link": data["link"]
            })
            
    return recommendations