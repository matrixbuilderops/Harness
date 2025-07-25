import os
import shutil
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
VERIFY_DIR = os.path.join(ROOT_DIR, "VerificationSessions")
BUILDER_DIR = os.path.join(ROOT_DIR, "BuilderSessions")
MATH_DIR = os.path.join(ROOT_DIR, "MathSessions")
UPDATE_MODE = False

# === SESSION SETUP ===

def create_session_dir(base_dir):
    ts = datetime.now().strftime("Update_%Y-%m-%d_%H-%M-%S") if UPDATE_MODE else datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    path = os.path.join(base_dir, ts)
    for sub in ("cache", "logs", "output", "output/verified_files", "update"):
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

def get_math_cache():
    latest = find_latest_dir(MATH_DIR)
    path = os.path.join(latest, "global_cache.txt")
    with open(path, "r", encoding="utf-8", errors="ignore") as f:
        return f.read()

def get_builder_outputs():
    latest = find_latest_dir(BUILDER_DIR)
    return [os.path.join(latest, "output", f) for f in os.listdir(os.path.join(latest, "output")) if f.endswith(".py")]

def read_text(path):
    with open(path, "r", encoding="utf-8", errors="ignore") as f:
        return f.read()

def write_text(path, content):
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)

# === MODEL I/O ===

async def call_model(session, prompt):
    payload = {"model": MODEL_NAME, "prompt": prompt}
    async with session.post(MODEL_API_URL, json=payload) as resp:
        return await resp.text()

def call_local_model(prompt):
    result = subprocess.run([MODEL_PATH, "run", MODEL_NAME], input=prompt, capture_output=True, text=True)
    return result.stdout.strip()

async def verify_script(script_path, math_text, log_path, cache_path, output_dir, index, total):
    script_name = os.path.basename(script_path)
    code = read_text(script_path)

    group_pct = int((index + 1) / total * 100)
    print(f"[VERIFY {index + 1}/{total}] {script_name} — {group_pct}%")

    prompt = f"""
You are the verification harness. Using the canonical math knowledge below, determine if the provided Python script is logically correct, functionally valid, and compliant with the architecture.

Respond with:
1. PASS/FAIL
2. List any violations
3. Suggested corrections if applicable

Math Canon:
{math_text}

Script to Verify:
{code}
"""

    if USE_API:
        async with aiohttp.ClientSession() as session:
            result = await call_model(session, prompt)
    else:
        result = call_local_model(prompt)

    result_path = os.path.join(output_dir, f"{script_name}_VERIFIED.txt")
    write_text(result_path, result)
    shutil.copy2(script_path, os.path.join(output_dir, "verified_files", script_name))

    with open(log_path, "a", encoding="utf-8") as flog:
        flog.write(f"[{script_name}] Verified → {result_path}\n")
    with open(cache_path, "a", encoding="utf-8") as fcache:
        fcache.write(f"[PROMPT: {script_name}]\n{prompt}\n\n")
    with open(os.path.join(os.path.dirname(cache_path), "global_cache.txt"), "a", encoding="utf-8") as fg:
        fg.write(f"[{script_name}] Verification Result\n{result}\n\n")

# === HARNESS EXECUTION ===

async def main():
    session = create_session_dir(VERIFY_DIR)
    if UPDATE_MODE:
        latest_prev = find_latest_dir(VERIFY_DIR)
        copy_previous_data(latest_prev, session)

    log_path = os.path.join(session, "logs", "log.txt")
    cache_path = os.path.join(session, "cache", "cache.txt")
    output_dir = os.path.join(session, "output")

    math_cache = get_math_cache()
    builder_outputs = get_builder_outputs()

    await asyncio.gather(*(verify_script(script,
                                         math_cache,
                                         log_path,
                                         cache_path,
                                         output_dir,
                                         i,
                                         len(builder_outputs))
                           for i, script in enumerate(builder_outputs)))

if __name__ == "__main__":
    asyncio.run(main())

