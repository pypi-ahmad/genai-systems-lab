from pathlib import Path

SUPPORTED_EXTENSIONS = {".txt", ".md"}


def load_documents(folder_path: str) -> list[dict]:
    folder = Path(folder_path)
    if not folder.is_dir():
        raise ValueError(f"Not a valid directory: {folder_path}")

    documents = []
    for file_path in sorted(folder.rglob("*")):
        if file_path.is_file() and file_path.suffix.lower() in SUPPORTED_EXTENSIONS:
            text = file_path.read_text(encoding="utf-8")
            if not text.strip():
                continue
            documents.append({
                "text": text,
                "source": str(file_path),
            })
    return documents
