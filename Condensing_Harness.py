import os
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
DEDUP_SESSIONS_DIR = os.path.join(ROOT_DIR, "DeduplicationSessions")
CONDENSE_SESSIONS_DIR = os.path.join(ROOT_DIR, "CondensingSessions")
UPDATE_MODE = False

# === HARNESS STRUCTURE ===

def create_session_dir(base_dir):
    timestamp = datetime.now().strftime("Update_%Y-%m-%d_%H-%M-%S") if UPDATE_MODE else datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    path = os.path.join(base_dir, timestamp)
    for sub in ("cache", "logs", "output", "output/condensed", "update"):
        os.makedirs(os.path.join(path, sub), exist_ok=True)
    open(os.path.join(path, "global_cache.txt"), "a").close()
    return path

def find_latest_session(base_dir):
    sessions = [s for s in os.listdir(base_dir) if os.path.isdir(os.path.join(base_dir, s))]
    return max(sessions, default="", key=lambda s: os.path.getmtime(os.path.join(base_dir, s)))

def copy_previous_data(prev_dir, update_dir):
    for sub in ("cache", "logs", "output", "global_cache.txt"):
        src = os.path.join(prev_dir, sub)
        dst = os.path.join(update_dir, "update", sub) if os.path.isdir(src) else os.path.join(update_dir, "update", os.path.basename(src))
        if os.path.isdir(src):
            shutil.copytree(src, dst, dirs_exist_ok=True)
        elif os.path.isfile(src):
            shutil.copy2(src, dst)

def get_variant_groups():
    latest_dedup = os.path.join(DEDUP_SESSIONS_DIR, find_latest_session(DEDUP_SESSIONS_DIR), "output", "variants")
    return [os.path.join(latest_dedup, d) for d in os.listdir(latest_dedup) if os.path.isdir(os.path.join(latest_dedup, d))]

def read_group_files(group_path):
    texts = []
    for file in os.listdir(group_path):
        full_path = os.path.join(group_path, file)
        with open(full_path, "r", encoding="utf-8", errors="ignore") as f:
            texts.append(f.read())
    return texts

def chunk_text(text, size):
    return [text[i:i + size] for i in range(0, len(text), size)]

async def call_model_api(session, prompt):
    payload = {"model": MODEL_NAME, "prompt": prompt}
    async with session.post(MODEL_API_URL, json=payload) as response:
        return await response.text()

def call_model_subprocess(prompt):
    result = subprocess.run([MODEL_PATH, "run", MODEL_NAME], input=prompt, capture_output=True, text=True)
    return result.stdout.strip()

async def condense_group(group_path, output_dir, cache_path, group_index, total_groups, log_path):
    files = read_group_files(group_path)
    group_pct = int((group_index + 1) / total_groups * 100)
    group_msg = f"[GROUP {group_index + 1}/{total_groups}] {os.path.basename(group_path)} ({group_pct}%)"
    print(group_msg)
    with open(log_path, "a", encoding="utf-8") as flog:
        flog.write(group_msg + "\n")

    group_text = "\n\n---\n\n".join(files)
    chunks = chunk_text(group_text, 2000)
    summarized_chunks = []

    async with aiohttp.ClientSession() as session:
        for idx, chunk in enumerate(chunks):
            sub_pct = int((idx + 1) / len(chunks) * 100)
            chunk_msg = f"  └─[CHUNK {idx + 1}/{len(chunks)}] ({sub_pct}%)"
            print(chunk_msg)
            with open(log_path, "a", encoding="utf-8") as flog:
                flog.write(chunk_msg + "\n")
            prompt = f"Part {idx+1}: Here is a segment of multiple similar scripts:\n\n{chunk}\n\nSummarize their common logic."
            output = await call_model_api(session, prompt) if USE_API else call_model_subprocess(prompt)
            summarized_chunks.append(output)
            with open(cache_path, "a", encoding="utf-8") as fc:
                fc.write(f"[SUMMARY CHUNK {idx+1}]\n{output}\n\n")

    final_prompt = "Combine these summaries into a single canonical version of the shared script logic:\n\n" + "\n\n".join(summarized_chunks)
    final_output = await call_model_api(session, final_prompt) if USE_API else call_model_subprocess(final_prompt)

    group_name = os.path.basename(group_path)
    out_path = os.path.join(output_dir, f"{group_name}_canonical.py")
    with open(out_path, "w", encoding="utf-8") as fout:
        fout.write(final_output)

    with open(log_path, "a", encoding="utf-8") as flog:
        flog.write(f"[{group_name}] condensed → {os.path.basename(out_path)}\n")

    with open(os.path.join(os.path.dirname(cache_path), "..", "global_cache.txt"), "a", encoding="utf-8") as fg:
        fg.write(f"[{group_name}] Canonical Summary:\n{final_output}\n\n")

async def main():
    session_path = create_session_dir(CONDENSE_SESSIONS_DIR)
    if UPDATE_MODE:
        latest_prev = os.path.join(CONDENSE_SESSIONS_DIR, find_latest_session(CONDENSE_SESSIONS_DIR))
        copy_previous_data(latest_prev, session_path)

    variant_groups = get_variant_groups()
    cache_path = os.path.join(session_path, "cache", "cache.txt")
    output_path = os.path.join(session_path, "output", "condensed")
    log_path = os.path.join(session_path, "logs", "log.txt")

    await asyncio.gather(*(condense_group(g, output_path, cache_path, idx, len(variant_groups), log_path) for idx, g in enumerate(variant_groups)))

if __name__ == "__main__":
    asyncio.run(main())

