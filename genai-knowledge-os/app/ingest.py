import os


SUPPORTED_EXTENSIONS = {".txt", ".md"}


def load_documents(folder_path: str) -> list[dict]:
    documents = []
    for root, _, files in os.walk(folder_path):
        for filename in sorted(files):
            ext = os.path.splitext(filename)[1].lower()
            if ext not in SUPPORTED_EXTENSIONS:
                continue
            file_path = os.path.join(root, filename)
            with open(file_path, "r", encoding="utf-8") as f:
                text = f.read()
            if not text.strip():
                continue
            documents.append({
                "text": text,
                "source": file_path,
            })
    return documents