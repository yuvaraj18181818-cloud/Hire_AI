def evaluate_skills(skill_results):
    total = len(skill_results)
    matched = sum(1 for s in skill_results.values() if s["present"])

    return {
        "total_skills": total,
        "matched_skills": matched,
        "missing_skills": total - matched,
        "coverage_percent": round((matched / total) * 100, 2)
    }
