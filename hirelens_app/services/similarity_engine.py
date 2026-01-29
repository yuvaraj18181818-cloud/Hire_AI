from sklearn.metrics.pairwise import cosine_similarity
from .embedding import get_embedding

def resume_similarity(resume_text, requirements_text):
    resume_emb = get_embedding(resume_text)
    req_emb = get_embedding(requirements_text)
    return float(cosine_similarity(resume_emb, req_emb)[0][0])
