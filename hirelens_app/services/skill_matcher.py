from sklearn.metrics.pairwise import cosine_similarity
from nltk.tokenize import sent_tokenize
from .embedding import get_embedding
import numpy as np

SKILL_THRESHOLD = 0.5

def detect_skills(resume_text, skill_set):
    sentences = sent_tokenize(resume_text)
    sentence_embeddings = np.vstack([get_embedding(s) for s in sentences])

    results = {}

    for skill, keywords in skill_set.items():
        keyword_match = any(kw in resume_text for kw in keywords)

        skill_embedding = get_embedding(" ".join(keywords))
        similarities = cosine_similarity(skill_embedding, sentence_embeddings)[0]

        matched = [
            sentences[i]
            for i, score in enumerate(similarities)
            if score >= SKILL_THRESHOLD
        ]

        results[skill] = {
            "present": keyword_match or bool(matched),
            "score": float(max(similarities)),
            "evidence": matched[:3]
        }

    return results
