def build_requirements(skills, experience):
    return {
        "skills": {s.lower(): [s.lower()] for s in skills},
        "experience": experience
    }
