from analyzer import extract_text, analyze

with open("resume_sample_student8ea47e04a8fe67e6b7acff0000376a3b.pdf", "rb") as f:
    text = extract_text(f)
print("Text length:", len(text))
print(text[:300])

print(analyze(text, "Python developer intern. FastAPI, SQL, Git."))