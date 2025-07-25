import os
import hashlib
from datetime import datetime
import subprocess
from docx import Document

CONDENSED_DIR = "CondensingSessions"
DESIGN_GUIDE = "DesignGuide.docx"
MODEL_PATH = "/usr/local/bin/ollama"
MODEL_NAME = "mixtral:8x7b-instruct-v0.1-q6_K"

SESSION_ROOT = "BuildSessions"
TIMESTAMP = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
SESSION_PATH = os.path.join(SESSION_ROOT, TIMESTAMP)

COMPONENT_DIR = os.path.join(SESSION_PATH, "components")
LOG_DIR = os.path.join(SESSION_PATH, "logs")
CACHE_DIR = os.path.join(SESSION_PATH, "cache")
OUTPUT_DIR = os.path.join(SESSION_PATH, "output")
GLOBAL_CACHE_FILE = os.path.join(SESSION_PATH, "global_cache.txt")

os.makedirs(COMPONENT_DIR, exist_ok=True)
os.makedirs(LOG_DIR, exist_ok=True)
os.makedirs(CACHE_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)


def hash_content(text):
    return hashlib.sha256(text.encode('utf-8')).hexdigest()


def load_design_guide(path):
    doc = Document(path)
    return "\n".join(para.text.strip() for para in doc.paragraphs if para.text.strip())


def write(path, content):
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)


def append(path, content):
    with open(path, 'a', encoding='utf-8') as f:
        f.write(content + "\n")


def find_latest_condensed():
    sessions = sorted(os.listdir(CONDENSED_DIR), reverse=True)
    for session in sessions:
        path = os.path.join(CONDENSED_DIR, session, "condensed")
        if os.path.exists(path):
            return path
    return None


def build_component(chunk_text, design_context):
    prompt = (
        "You are a recursive intelligence trained to synthesize software components. "
        "Using the condensed logic provided, build the corresponding code component (QTL preferred, Python acceptable). "
        "Incorporate design principles from the following guide:\n\n"
        f"{design_context}\n\n"
        "--- Condensed Logic ---\n"
        f"{chunk_text}\n\n"
        "Begin building."
    )

    command = [MODEL_PATH, "run", MODEL_NAME]
    process = subprocess.Popen(command, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    stdout_raw, stderr_raw = process.communicate(input=prompt.encode('utf-8'))

    stdout = stdout_raw.decode('utf-8', errors='replace').strip()
    stderr = stderr_raw.decode('utf-8', errors='ignore').strip()

    if not stdout:
        stdout = "[ERROR] Failed to generate component."

    return stdout, prompt, stderr


def main():
    design_context = load_design_guide(DESIGN_GUIDE)
    condensed_path = find_latest_condensed()
    if not condensed_path:
        print("[FATAL] No condensed directory found.")
        return

    for filename in os.listdir(condensed_path):
        if not filename.endswith(".txt"):
            continue

        base_name = os.path.splitext(filename)[0]
        with open(os.path.join(condensed_path, filename), 'r', encoding='utf-8') as f:
            chunk_text = f.read()

        output, prompt_used, stderr = build_component(chunk_text, design_context)

        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        component_path = os.path.join(COMPONENT_DIR, f"{base_name}.qtl")
        log_path = os.path.join(LOG_DIR, "log.txt")
        output_path = os.path.join(OUTPUT_DIR, "output.txt")
        cache_path = os.path.join(CACHE_DIR, "cache.txt")

        write(component_path, output)
        append(log_path, f"[{timestamp}] Built component: {filename}")
        append(output_path, f"=== {base_name} ===\n{output}\n")
        append(cache_path, f"=== {base_name} ===\nPrompt SHA256: {hash_content(prompt_used)}\n{prompt_used}\n--- Output SHA256: {hash_content(output)} ---\n{output}\n")
        append(GLOBAL_CACHE_FILE, f"=== GLOBAL ENTRY: {base_name} ===\nPrompt SHA256: {hash_content(prompt_used)}\n{prompt_used}\n--- Output SHA256: {hash_content(output)} ---\n{output}\n")

    print("=== BUILDER HARNESS COMPLETE ===")
    print("Session folder:", SESSION_PATH)


if __name__ == "__main__":
    main()
