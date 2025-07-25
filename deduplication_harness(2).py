import os
import zipfile
import difflib
import hashlib
from datetime import datetime

ROOT_SESSIONS = "MathSessions"
DEDUPE_SESSIONS = "DeduplicationSessions"
FILES_DIR = "Files"

THRESHOLD = 0.95  # Similarity threshold for deduplication

def get_most_recent_session():
    sessions = [d for d in os.listdir(ROOT_SESSIONS) if os.path.isdir(os.path.join(ROOT_SESSIONS, d))]
    sessions.sort(reverse=True)
    return os.path.join(ROOT_SESSIONS, sessions[0]) if sessions else None

def get_all_cache_files(session_path):
    cache_files = []
    for sub in os.listdir(session_path):
        sub_path = os.path.join(session_path, sub, "cache", "cache.txt")
        if os.path.exists(sub_path):
            cache_files.append((sub, sub_path))
    return cache_files

def extract_zip_files():
    extracted = []
    for file in os.listdir(FILES_DIR):
        if file.endswith(".zip"):
            dest = os.path.join(FILES_DIR, file.replace(".zip", ""))
            os.makedirs(dest, exist_ok=True)
            with zipfile.ZipFile(os.path.join(FILES_DIR, file), 'r') as zip_ref:
                zip_ref.extractall(dest)
            extracted.append(dest)
    return extracted

def hash_content(text):
    return hashlib.sha256(text.encode('utf-8')).hexdigest()

def compare_content(text1, text2):
    return difflib.SequenceMatcher(None, text1, text2).ratio()

def load_all_known_chunks(cache_files):
    known_chunks = {}
    for label, path in cache_files:
        with open(path, 'r', encoding='utf-8') as f:
            content = f.read()
        chunks = content.split("==== Chunk")
        for chunk in chunks:
            chunk = chunk.strip()
            if chunk:
                h = hash_content(chunk)
                known_chunks[h] = chunk
    return known_chunks

def deduplicate_folder(folder_path, known_chunks):
    unique_chunks = {}
    skipped = 0
    for root, _, files in os.walk(folder_path):
        for file in files:
            if file.endswith(".txt"):
                full_path = os.path.join(root, file)
                with open(full_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                is_duplicate = False
                for existing in known_chunks.values():
                    sim = compare_content(content, existing)
                    if sim >= THRESHOLD:
                        is_duplicate = True
                        skipped += 1
                        break
                if not is_duplicate:
                    h = hash_content(content)
                    unique_chunks[h] = content
    return unique_chunks, skipped

def save_deduped_output(results, session_folder):
    output_dir = os.path.join(DEDUPE_SESSIONS, session_folder)
    os.makedirs(output_dir, exist_ok=True)
    for i, (h, content) in enumerate(results.items(), 1):
        with open(os.path.join(output_dir, f"deduped_{i}.txt"), 'w', encoding='utf-8') as f:
            f.write(content)

def main():
    now = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    session_folder = now
    os.makedirs(DEDUPE_SESSIONS, exist_ok=True)

    latest_session = get_most_recent_session()
    if not latest_session:
        print("No previous MathSessions found.")
        return

    cache_files = get_all_cache_files(latest_session)
    known_chunks = load_all_known_chunks(cache_files)

    extracted_dirs = extract_zip_files()

    total_unique = {}
    total_skipped = 0

    for d in extracted_dirs:
        results, skipped = deduplicate_folder(d, known_chunks)
        total_skipped += skipped
        total_unique.update(results)

    save_deduped_output(total_unique, session_folder)
    print(f"[DEDUPLICATION COMPLETE] Unique files: {len(total_unique)}, Skipped duplicates: {total_skipped}")

if __name__ == "__main__":
    main()
