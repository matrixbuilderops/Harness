import os
import hashlib
import difflib
import json
from datetime import datetime

DEDUP_ROOT = "DeduplicationSessions"
SESSION_ROOT = "CondensingSessions"

TIMESTAMP = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
SESSION_PATH = os.path.join(SESSION_ROOT, TIMESTAMP)
CONDENSED_DIR = os.path.join(SESSION_PATH, "condensed")
LOG_DIR = os.path.join(SESSION_PATH, "logs")
CACHE_DIR = os.path.join(SESSION_PATH, "cache")
OUTPUT_DIR = os.path.join(SESSION_PATH, "output")

os.makedirs(CONDENSED_DIR, exist_ok=True)
os.makedirs(LOG_DIR, exist_ok=True)
os.makedirs(CACHE_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)

GLOBAL_CACHE_FILE = os.path.join(SESSION_PATH, "global_cache.txt")

def hash_content(text):
    return hashlib.sha256(text.encode('utf-8')).hexdigest()

def write_to_file(path, content):
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)

def append_to_file(path, content):
    with open(path, 'a', encoding='utf-8') as f:
        f.write(content + "\n")

def get_latest_dedup_session():
    sessions = sorted(os.listdir(DEDUP_ROOT))
    return os.path.join(DEDUP_ROOT, sessions[-1]) if sessions else None

def load_variants(variant_dir):
    sets = {}
    for fname in sorted(os.listdir(variant_dir)):
        if "_var" not in fname:
            continue
        base = fname.split("_var")[0]
        if base not in sets:
            sets[base] = []
        with open(os.path.join(variant_dir, fname), 'r', encoding='utf-8', errors='ignore') as f:
            sets[base].append((fname, f.read()))
    return sets

def condense_variants(variant_group):
    best = variant_group[0][1]
    best_name = variant_group[0][0]
    best_score = 0
    for name, text in variant_group[1:]:
        score = difflib.SequenceMatcher(None, best, text).ratio()
        if score < 0.95 and len(text) > len(best):
            best = text
            best_name = name
            best_score = score
    return best_name, best

def process():
    dedup_path = get_latest_dedup_session()
    variant_dir = os.path.join(dedup_path, "variant_sets")
    log_path = os.path.join(LOG_DIR, "log.txt")
    cache_path = os.path.join(CACHE_DIR, "cache.txt")
    manifest = {}

    variant_sets = load_variants(variant_dir)

    for i, (basename, variants) in enumerate(variant_sets.items(), start=1):
        print(f"[CONDENSING] Set {i}/{len(variant_sets)} - {basename}")
        best_name, best_version = condense_variants(variants)
        out_path = os.path.join(CONDENSED_DIR, f"{basename}_condensed.txt")
        write_to_file(out_path, best_version)

        h = hash_content(best_version)
        append_to_file(GLOBAL_CACHE_FILE, f"HASH: {h}")
        append_to_file(cache_path, f"HASH: {h}")

        log_entry = (
            f"==== CONDENSE LOG {basename} ===="
            f"\nSelected: {best_name}\nHash: {h}\n---\n{best_version}\n==== END ===="
        )
        append_to_file(log_path, log_entry)

        manifest[basename] = {
            "variant_count": len(variants),
            "selected": best_name,
            "hash": h
        }

    manifest_path = os.path.join(SESSION_PATH, "manifest.json")
    with open(manifest_path, 'w', encoding='utf-8') as f:
        json.dump(manifest, f, indent=2)

if __name__ == "__main__":
    process()
    print(f"[DONE] Condensing complete. Session stored in: {SESSION_PATH}")
