import os
import zipfile
import shutil
import hashlib
import asyncio
import aiohttp
import subprocess
import psutil
from datetime import datetime

# === CONFIGURATION ===
USE_API = True
MODEL_API_URL = "http://localhost:11434/api/generate"
MODEL_PATH = "/usr/local/bin/ollama"
MODEL_NAME = "mixtral:8x7b-instruct-v0.1-q6_K"

ROOT_DIR = os.getcwd()
FILES_DIR = os.path.join(ROOT_DIR, "Files")
MATH_SESSIONS_DIR = os.path.join(ROOT_DIR, "MathSessions")
DEDUP_SESSIONS_DIR = os.path.join(ROOT_DIR, "DeduplicationSessions")
UPDATE_MODE = False

# === HARNESS STRUCTURE ===

def create_session_dir(base_dir):
    timestamp = datetime.now().strftime("Update_%Y-%m-%d_%H-%M-%S") if UPDATE_MODE else datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    path = os.path.join(base_dir, timestamp)
    for sub in ("cache", "logs", "output", "output/unique", "output/variants", "duplicates", "update"):
        os.makedirs(os.path.join(path, sub), exist_ok=True)
    open(os.path.join(path, "global_cache.txt"), "a").close()
    return path

def find_latest_session(base_dir):
    sessions = [s for s in os.listdir(base_dir) if os.path.isdir(os.path.join(base_dir, s))]
    return max(sessions, default="", key=lambda s: os.path.getmtime(os.path.join(base_dir, s)))

def load_math_global_cache():
    latest_math = os.path.join(MATH_SESSIONS_DIR, find_latest_session(MATH_SESSIONS_DIR))
    path = os.path.join(latest_math, "global_cache.txt")
    with open(path, "r", encoding="utf-8") as f:
        return f.read()

def chunk_text(text, size):
    return [text[i:i + size] for i in range(0, len(text), size)]

async def call_model_api(session, prompt):
    payload = {"model": MODEL_NAME, "prompt": prompt}
    async with session.post(MODEL_API_URL, json=payload) as response:
        return await response.text()

def call_model_subprocess(prompt):
    result = subprocess.run([MODEL_PATH, "run", MODEL_NAME], input=prompt, capture_output=True, text=True)
    return result.stdout.strip()

async def process_math_bootstrap(cache_text, output_paths):
    ram = psutil.virtual_memory().available // (1024 * 1024)
    chunk_size = 2000 if ram > 16000 else 1000
    chunks = chunk_text(cache_text, chunk_size)
    async with aiohttp.ClientSession() as session:
        for idx, chunk in enumerate(chunks):
            pct = int((idx + 1) / len(chunks) * 100)
            print(f"[MATH_BOOTSTRAP] Chunk {idx + 1}/{len(chunks)} ({pct}%)")
            prompt = f"You are priming on prior mathematical context. Digest this: \n\n{chunk.strip()}"
            output = await call_model_api(session, prompt) if USE_API else call_model_subprocess(prompt)
            with open(output_paths["cache"], "a") as fc:
                fc.write(f"[MATH_BOOTSTRAP CHUNK {idx+1}]\n{output}\n\n")

def hash_file_contents(path):
    with open(path, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()

def read_text_file(path):
    with open(path, "r", encoding="utf-8", errors="ignore") as f:
        return f.read()

def write_dedup_output(content, group_id, output_base):
    group_dir = os.path.join(output_base, "output", "variants", f"group_{group_id}")
    os.makedirs(group_dir, exist_ok=True)
    fname = f"variant_{group_id}_{hashlib.md5(content.encode()).hexdigest()[:8]}.txt"
    with open(os.path.join(group_dir, fname), "w", encoding="utf-8") as f:
        f.write(content)

async def summarize_logic(content):
    prompt = f"Summarize the logic of the following code:\n\n{content}"
    async with aiohttp.ClientSession() as session:
        return await call_model_api(session, prompt) if USE_API else call_model_subprocess(prompt)

async def classify_file(fname, text, hashes_seen, logic_seen, logic_summaries, session_path):
    content_hash = hashlib.sha256(text.encode()).hexdigest()
    if content_hash in hashes_seen:
        with open(os.path.join(session_path, "duplicates", f"{content_hash}.txt"), "w", encoding="utf-8") as f:
            f.write(text)
        return f"{fname}: duplicate"
    hashes_seen.add(content_hash)

    summary = await summarize_logic(text)
    for idx, prior_summary in enumerate(logic_summaries):
        if summary[:100] in prior_summary:
            write_dedup_output(text, idx, session_path)
            return f"{fname}: variant of group_{idx}"

    logic_seen.append(text)
    logic_summaries.append(summary)
    uid = hashlib.md5(text.encode()).hexdigest()[:8]
    with open(os.path.join(session_path, "output", "unique", f"{uid}.txt"), "w", encoding="utf-8") as f:
        f.write(text)
    return f"{fname}: unique"

async def process_zip_file(zip_path, session_path, hashes_seen, logic_seen, logic_summaries, zip_index, total_zips):
    print(f"\n[ZIP {zip_index + 1}/{total_zips}] {os.path.basename(zip_path)} ({int((zip_index + 1)/total_zips*100)}%)")
    temp_dir = os.path.join(session_path, "temp_extract")
    if os.path.exists(temp_dir):
        shutil.rmtree(temp_dir)
    os.makedirs(temp_dir, exist_ok=True)

    with zipfile.ZipFile(zip_path, "r") as zip_ref:
        zip_ref.extractall(temp_dir)

    files_to_process = []
    for root, _, files in os.walk(temp_dir):
        for fname in files:
            fpath = os.path.join(root, fname)
            files_to_process.append((fpath, fname))

    async def process_single_file(findex, total_files, fpath, fname):
        text = read_text_file(fpath)
        result = await classify_file(fname, text, hashes_seen, logic_seen, logic_summaries, session_path)
        print(f"[FILE {findex + 1}/{total_files} ({int((findex + 1)/total_files*100)}%)] {result}")
        with open(os.path.join(session_path, "logs", "log.txt"), "a") as log:
            log.write(f"{result}\n")

    await asyncio.gather(*(process_single_file(i, len(files_to_process), p, n) for i, (p, n) in enumerate(files_to_process)))
    shutil.rmtree(temp_dir)

async def main():
    session_path = create_session_dir(DEDUP_SESSIONS_DIR)
    paths = {"cache": os.path.join(session_path, "cache", "cache.txt")}
    math_cache = load_math_global_cache()
    await process_math_bootstrap(math_cache, paths)

    zip_files = [f for f in os.listdir(FILES_DIR) if f.endswith(".zip")]
    hashes_seen = set()
    logic_seen = []
    logic_summaries = []

    for i, zip_file in enumerate(zip_files):
        full_path = os.path.join(FILES_DIR, zip_file)
        await process_zip_file(full_path, session_path, hashes_seen, logic_seen, logic_summaries, i, len(zip_files))

if __name__ == "__main__":
    asyncio.run(main())

