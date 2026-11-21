from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from llm import ask_llm


def chunk_text(text, size=800, overlap=150):
    chunks, start = [], 0
    while start < len(text):
        chunks.append(text[start:start + size].strip())
        start += size - overlap
    return [c for c in chunks if len(c) > 50]


def top_chunks(question, chunks, k=3):
    if not chunks:
        return []
    try:
        vec = TfidfVectorizer(stop_words="english")
        matrix = vec.fit_transform(chunks + [question])
    except ValueError:                       # sawal mein koi kaam ka shabd nahi
        return chunks[:k]
    scores = cosine_similarity(matrix[-1], matrix[:-1]).flatten()
    best = scores.argsort()[::-1][:k]
    if len(best) == 0:
        return []
    return [chunks[int(i)] for i in best[:k]]


def answer(question, context_chunks):
    context = "\n---\n".join(context_chunks)
    prompt = ("Answer only from the provided document text. Use simple, clear language. "
              "Summarize the document or answer the question directly. "
              'Say "I could not find this in the document" only when the provided text truly does not contain it.\n\n'
              f"DOCUMENT TEXT:\n{context}\n\nQUESTION: {question}")
    return ask_llm(prompt)
