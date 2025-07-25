# deduplication_harness.py

import os
import zipfile
import hashlib
import difflib
from datetime import datetime
from pathlib import Path
from docx import Document

DEDUP_ROOT = "DeduplicationSessions"
INPUT_DIR = "Files"
MATH_SESSION_ROOT = "MathSessions"

SIMILARITY_THRESHOLD = 0.95


def extract_chunks_from_txt(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    return [chunk.strip() for chunk in content.split("\n\n") if chunk.strip()]


def extract_chunks_from_docx(docx_path):
    doc = Document(docx_path)
    buffer, chunks = [], []
    for para in doc.paragraphs:
        text = para.text.strip()
        if text == "" and buffer:
            chunks.append("\n".join(buffer))
            buffer = []
        elif text:
            buffer.append(text)
    if buffer:
        chunks.append("\n".join(buffer))
    return chunks


def hash_chunk(text):
    return hashlib.sha256(text.encode('utf-8')).hexdigest()


def is_similar(a, b):
    return difflib.SequenceMatcher(None, a, b).ratio() >= SIMILARITY_THRESHOLD


def gather_prior_chunks():
    prior_chunks = []
    session_dirs = sorted(Path(MATH_SESSION_ROOT).glob("*/"), key=os.path.getmtime, reverse=True)
    if not session_dirs:
        return prior_chunks

    most_recent = session_dirs[0]
    for folder in most_recent.iterdir():
        cache_file = folder / "cache" / "cache.txt"
        if cache_file.exists():
            with open(cache_file, 'r', encoding='utf-8') as f:
                raw = f.read()
                chunks = [chunk.strip() for chunk in raw.split("\n\n") if chunk.strip()]
                prior_chunks.extend(chunks)
    return prior_chunks


def recursive_extract_zip(zip_path, extract_to):
    with zipfile.ZipFile(zip_path, 'r') as z:
        z.extractall(extract_to)


def walk_files(root_dir):
    for dirpath, _, filenames in os.walk(root_dir):
        for f in filenames:
            if f.endswith('.txt') or f.endswith('.docx'):
                yield os.path.join(dirpath, f)


def process():
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    session_dir = os.path.join(DEDUP_ROOT, timestamp)
    os.makedirs(session_dir, exist_ok=True)

    temp_extract_root = os.path.join(session_dir, "unzipped")
    os.makedirs(temp_extract_root, exist_ok=True)

    # Step 1: Extract all zip files
    for zip_file in Path(INPUT_DIR).glob("*.zip"):
        extract_dir = os.path.join(temp_extract_root, zip_file.stem)
        os.makedirs(extract_dir, exist_ok=True)
        recursive_extract_zip(zip_file, extract_dir)

    # Step 2: Load prior known chunks (cache memory)
    prior_chunks = gather_prior_chunks()

    unique_chunks = []
    chunk_sources = {}

    # Step 3: Walk all files and deduplicate
    for file_path in walk_files(temp_extract_root):
        if file_path.endswith(".txt"):
            chunks = extract_chunks_from_txt(file_path)
        elif file_path.endswith(".docx"):
            chunks = extract_chunks_from_docx(file_path)
        else:
            continue

        for chunk in chunks:
            if any(is_similar(chunk, known) for known in prior_chunks):
                continue
            if any(is_similar(chunk, known) for known in unique_chunks):
                continue
            unique_chunks.append(chunk)
            chunk_sources[chunk] = file_path

    # Step 4: Write output + manifest
    output_path = os.path.join(session_dir, "deduplicated.txt")
    with open(output_path, 'w', encoding='utf-8') as out:
        for chunk in unique_chunks:
            out.write(f"==== Source: {chunk_sources[chunk]} ====
{chunk}\n\n")

    manifest_path = os.path.join(session_dir, "manifest.txt")
    with open(manifest_path, 'w', encoding='utf-8') as m:
        m.write("Deduplication complete.\n")
        m.write(f"Session: {session_dir}\n")
        m.write(f"Unique chunks: {len(unique_chunks)}\n")
        m.write(f"Sources analyzed: {len(list(walk_files(temp_extract_root)))}\n")

    print(f"Deduplication session complete. Results in: {session_dir}")


if __name__ == "__main__":
    process()
