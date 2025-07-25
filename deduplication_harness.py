import os
import zipfile
import hashlib
from pathlib import Path
from datetime import datetime
from docx import Document

ROOT_INPUT_FOLDER = "Files"
SESSION_ROOT = "DeduplicationSessions"
TIMESTAMP = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
SESSION_PATH = os.path.join(SESSION_ROOT, TIMESTAMP)
EXTRACTION_PATH = os.path.join(SESSION_PATH, "extracted")
UNIQUE_DOCS_PATH = os.path.join(SESSION_PATH, "unique")

os.makedirs(EXTRACTION_PATH, exist_ok=True)
os.makedirs(UNIQUE_DOCS_PATH, exist_ok=True)

def extract_zip_recursively(zip_path, extract_to):
    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        zip_ref.extractall(extract_to)
    for root, _, files in os.walk(extract_to):
        for file in files:
            full_path = os.path.join(root, file)
            if zipfile.is_zipfile(full_path):
                subfolder = os.path.join(root, f"_unpacked_{file}")
                os.makedirs(subfolder, exist_ok=True)
                extract_zip_recursively(full_path, subfolder)

def hash_docx_content(docx_path):
    doc = Document(docx_path)
    text = "\n".join([para.text for para in doc.paragraphs if para.text.strip()])
    return hashlib.sha256(text.encode('utf-8')).hexdigest(), text

def find_unique_documents(folder):
    seen_hashes = set()
    unique_paths = []
    for root, _, files in os.walk(folder):
        for file in files:
            if file.endswith(".docx"):
                full_path = os.path.join(root, file)
                try:
                    content_hash, _ = hash_docx_content(full_path)
                    if content_hash not in seen_hashes:
                        seen_hashes.add(content_hash)
                        unique_paths.append(full_path)
                except Exception as e:
                    print(f"[ERROR] Could not process {full_path}: {e}")
    return unique_paths

def copy_unique_documents(paths):
    for i, path in enumerate(paths):
        filename = f"unique_{i+1}.docx"
        destination = os.path.join(UNIQUE_DOCS_PATH, filename)
        with open(path, 'rb') as src, open(destination, 'wb') as dst:
            dst.write(src.read())

def main():
    for file in os.listdir(ROOT_INPUT_FOLDER):
        if file.endswith(".zip"):
            extract_zip_recursively(os.path.join(ROOT_INPUT_FOLDER, file), EXTRACTION_PATH)

    unique_docs = find_unique_documents(EXTRACTION_PATH)
    copy_unique_documents(unique_docs)

    print(f"[INFO] Deduplication complete. {len(unique_docs)} unique files saved to: {UNIQUE_DOCS_PATH}")

if __name__ == "__main__":
    main()
