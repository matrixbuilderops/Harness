import zipfile
import os
import hashlib
import shutil
import json
from datetime import datetime

SESSION_ROOT = "DeduplicationSessions"
FILES_DIR = "files"
VALID_EXTENSIONS = {".qtl", ".py"}

TIMESTAMP = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
SESSION_PATH = os.path.join(SESSION_ROOT, TIMESTAMP)

UNIQUE_DIR = os.path.join(SESSION_PATH, "unique")
VARIANT_DIR = os.path.join(SESSION_PATH, "variant_sets")
LOG_DIR = os.path.join(SESSION_PATH, "logs")
CACHE_DIR = os.path.join(SESSION_PATH, "cache")
OUTPUT_DIR = os.path.join(SESSION_PATH, "output")
GLOBAL_CACHE_FILE = os.path.join(SESSION_PATH, "global_cache.txt")

os.makedirs(UNIQUE_DIR, exist_ok=True)
os.makedirs(VARIANT_DIR, exist_ok=True)
os.makedirs(LOG_DIR, exist_ok=True)
os.makedirs(CACHE_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)

def hash_content(text):
    return hashlib.sha256(text.encode('utf-8')).hexdigest()

def write_to_file(path, content):
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)

def append_to_file(path, content):
    with open(path, 'a', encoding='utf-8') as f:
        f.write(content + "\n")

def extract_zip(zip_path, extract_to):
    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        zip_ref.extractall(extract_to)

def collect_all_files(base_dir):
    all_files = []
    for root, _, files in os.walk(base_dir):
        for file in files:
            if os.path.splitext(file)[1] in VALID_EXTENSIONS:
                all_files.append(os.path.join(root, file))
    return all_files

def load_existing_hashes():
    seen = set()
    for session in os.listdir(SESSION_ROOT):
        path = os.path.join(SESSION_ROOT, session, "global_cache.txt")
        if os.path.exists(path):
            with open(path, 'r', encoding='utf-8') as f:
                for line in f:
                    if line.startswith("HASH:"):
                        seen.add(line.strip().split("HASH:")[1].strip())
    return seen

def process_files():
    log_path = os.path.join(LOG_DIR, "log.txt")
    cache_path = os.path.join(CACHE_DIR, "cache.txt")
    manifest = {}
    hash_to_files = {}

    seen_hashes = load_existing_hashes()

    for zip_file in sorted(os.listdir(FILES_DIR)):
        if not zip_file.endswith(".zip"):
            continue

        zip_path = os.path.join(FILES_DIR, zip_file)
        temp_extract = os.path.join(SESSION_PATH, "_temp")
        os.makedirs(temp_extract, exist_ok=True)
        extract_zip(zip_path, temp_extract)

        for file_path in collect_all_files(temp_extract):
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            h = hash_content(content)
            filename = os.path.basename(file_path)

            log_entry = f"[HASH: {h}] File: {filename} from {zip_file}"
            append_to_file(log_path, log_entry)

            if h in seen_hashes:
                manifest[filename] = {"status": "duplicate", "hash": h}
                continue

            append_to_file(GLOBAL_CACHE_FILE, f"HASH: {h}")
            append_to_file(cache_path, f"HASH: {h}")

            if h not in hash_to_files:
                hash_to_files[h] = []
            hash_to_files[h].append((filename, content))

        shutil.rmtree(temp_extract)

    for h, file_group in hash_to_files.items():
        if len(file_group) == 1:
            fname, content = file_group[0]
            out_path = os.path.join(UNIQUE_DIR, fname)
            write_to_file(out_path, content)
            manifest[fname] = {"status": "unique", "hash": h}
        else:
            for i, (fname, content) in enumerate(file_group):
                out_path = os.path.join(VARIANT_DIR, f"{fname}_var{i+1}.txt")
                write_to_file(out_path, content)
                manifest[f"{fname}_var{i+1}.txt"] = {"status": "variant", "hash": h}

    manifest_path = os.path.join(SESSION_PATH, "manifest.json")
    with open(manifest_path, 'w', encoding='utf-8') as f:
        json.dump(manifest, f, indent=2)

if __name__ == "__main__":
    process_files()
    print(f"[DONE] Deduplication complete. Session stored in: {SESSION_PATH}")
