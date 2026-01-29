def generate_improvement_plan(courses):
    if not courses:
        return "No skill gaps detected. Candidate is well aligned."

    plan_lines = [
        "PERSONALIZED SKILL IMPROVEMENT PLAN\n"
    ]

    for c in courses:
        plan_lines.append(
            f"- Improve **{c['skill'].capitalize()}** by enrolling in "
            f"{c['course']} ({c['link']})"
        )

    return "\n".join(plan_lines)
