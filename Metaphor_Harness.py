import os
import shutil
import asyncio
import aiohttp
import subprocess
import psutil
import docx
from datetime import datetime

# === CONFIGURATION ===
USE_API = True
MODEL_API_URL = "http://localhost:11434/api/generate"
MODEL_PATH = "/usr/local/bin/ollama"
MODEL_NAME = "mixtral:8x7b-instruct-v0.1-q6_K"

ROOT_DIR = os.getcwd()
METAPHOR_DIR = os.path.join(ROOT_DIR, "MetaphorSessions")
MATH_METAPHORS = os.path.join(ROOT_DIR, "MathMetaphors")
BUILDER_DIR = os.path.join(ROOT_DIR, "BuilderSessions")
UPDATE_MODE = False

# === SESSION SETUP ===

def create_session_dir(base_dir):
    ts = datetime.now().strftime("Update_%Y-%m-%d_%H-%M-%S") if UPDATE_MODE else datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    path = os.path.join(base_dir, ts)
    for sub in ("cache", "logs", "output/equations", "update"):
        os.makedirs(os.path.join(path, sub), exist_ok=True)
    open(os.path.join(path, "global_cache.txt"), "a").close()
    return path

def find_latest_dir(parent):
    dirs = [d for d in os.listdir(parent) if os.path.isdir(os.path.join(parent, d))]
    return os.path.join(parent, max(dirs, default="", key=lambda d: os.path.getmtime(os.path.join(parent, d))))

def copy_previous_data(prev, target):
    for sub in ("cache", "logs", "output", "global_cache.txt"):
        src = os.path.join(prev, sub)
        dst = os.path.join(target, "update", sub) if os.path.isdir(src) else os.path.join(target, "update", os.path.basename(src))
        if os.path.isdir(src):
            shutil.copytree(src, dst, dirs_exist_ok=True)
        elif os.path.isfile(src):
            shutil.copy2(src, dst)

# === FILE LOADING ===

def get_math_context():
    latest = find_latest_dir(BUILDER_DIR)
    path = os.path.join(latest, "global_cache.txt")
    with open(path, "r", encoding="utf-8", errors="ignore") as f:
        return f.read()

def get_all_docx(root):
    return [os.path.join(dp, f) for dp, _, filenames in os.walk(root) for f in filenames if f.endswith(".docx")]

def read_docx_chunks(path):
    doc = docx.Document(path)
    return [p.text.strip() for p in doc.paragraphs if p.text.strip()]

# === MODEL I/O ===

async def call_model(session, prompt):
    payload = {"model": MODEL_NAME, "prompt": prompt}
    async with session.post(MODEL_API_URL, json=payload) as resp:
        return await resp.text()

def call_local_model(prompt):
    result = subprocess.run([MODEL_PATH, "run", MODEL_NAME], input=prompt, capture_output=True, text=True)
    return result.stdout.strip()

async def interpret_metaphor_chunk(chunk_text, math_context, out_base, chunk_idx, total_chunks, file_name, log_path, cache_path):
    file_pct = int((chunk_idx + 1) / total_chunks * 100)
    print(f"[{file_name}] Chunk {chunk_idx + 1}/{total_chunks} — {file_pct}%")

    prompt = f"""
You are the metaphor harness. You receive a metaphorical math concept and must transcribe it into a formal, recursive, symbolic equation that an AI model can understand and build on.

Math Canon:
{math_context}

Metaphor:
{chunk_text}
"""

    if USE_API:
        async with aiohttp.ClientSession() as session:
            result = await call_model(session, prompt)
    else:
        result = call_local_model(prompt)

    chunk_file = os.path.join(out_base, f"{file_name}_chunk_{chunk_idx + 1}.txt")
    with open(chunk_file, "w", encoding="utf-8") as f:
        f.write(result)

    with open(log_path, "a", encoding="utf-8") as flog:
        flog.write(f"[{file_name}] Chunk {chunk_idx + 1} → {chunk_file}\n")
    with open(cache_path, "a", encoding="utf-8") as fcache:
        fcache.write(f"[PROMPT: {file_name} - Chunk {chunk_idx + 1}]\n{prompt}\n\n")
    with open(os.path.join(os.path.dirname(cache_path), "global_cache.txt"), "a", encoding="utf-8") as fg:
        fg.write(f"[{file_name}] Chunk {chunk_idx + 1} Result\n{result}\n\n")

# === HARNESS EXECUTION ===

async def main():
    session = create_session_dir(METAPHOR_DIR)
    if UPDATE_MODE:
        latest_prev = find_latest_dir(METAPHOR_DIR)
        copy_previous_data(latest_prev, session)

    log_path = os.path.join(session, "logs", "log.txt")
    cache_path = os.path.join(session, "cache", "cache.txt")
    output_dir = os.path.join(session, "output/equations")

    math_context = get_math_context()
    docx_files = get_all_docx(MATH_METAPHORS)

    tasks = []
    for doc in docx_files:
        base_name = os.path.splitext(os.path.basename(doc))[0]
        chunks = read_docx_chunks(doc)
        for i, chunk in enumerate(chunks):
            tasks.append(interpret_metaphor_chunk(chunk, math_context, output_dir, i, len(chunks), base_name, log_path, cache_path))

    await asyncio.gather(*tasks)

if __name__ == "__main__":
    asyncio.run(main())

