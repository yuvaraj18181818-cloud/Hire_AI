from sklearn.metrics.pairwise import cosine_similarity
from nltk.tokenize import sent_tokenize
from .embedding import get_embedding
import numpy as np

SKILL_THRESHOLD = 0.5

def match_skills(resume_text, skill_set):
    sentences = sent_tokenize(resume_text)
    sentence_embeddings = np.vstack([get_embedding(s) for s in sentences])

    results = {}

    for skill, keywords in skill_set.items():
        keyword_found = any(k in resume_text for k in keywords)

        skill_emb = get_embedding(" ".join(keywords))
        sims = cosine_similarity(skill_emb, sentence_embeddings)[0]

        evidence = [
            sentences[i]
            for i, s in enumerate(sims)
            if s >= SKILL_THRESHOLD
        ]

        results[skill] = {
            "present": keyword_found or bool(evidence),
            "score": float(max(sims)),
            "evidence": evidence[:3]
        }

    return results
