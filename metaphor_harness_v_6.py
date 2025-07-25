import os
import hashlib
import subprocess
from datetime import datetime
from docx import Document

INPUT_FOLDER = "MathMetaphors"
MODEL_PATH = "/usr/local/bin/ollama"
MODEL_NAME = "mixtral:8x7b-instruct-v0.1-q6_K"
GLOBAL_CACHE_ROOT = "BuildSessions"

SESSION_ROOT = "MetaphorSessions"
TIMESTAMP = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
SESSION_PATH = os.path.join(SESSION_ROOT, TIMESTAMP)

EQUATIONS_DIR = os.path.join(SESSION_PATH, "equations")
LOG_DIR = os.path.join(SESSION_PATH, "logs")
CACHE_DIR = os.path.join(SESSION_PATH, "cache")
OUTPUT_DIR = os.path.join(SESSION_PATH, "output")

for path in [EQUATIONS_DIR, LOG_DIR, CACHE_DIR, OUTPUT_DIR]:
    os.makedirs(path, exist_ok=True)


def hash_content(text):
    return hashlib.sha256(text.encode('utf-8')).hexdigest()


def append(path, content):
    with open(path, 'a', encoding='utf-8') as f:
        f.write(content + "\n")


def find_latest_global_cache():
    sessions = sorted(os.listdir(GLOBAL_CACHE_ROOT), reverse=True)
    for session in sessions:
        gc_path = os.path.join(GLOBAL_CACHE_ROOT, session, "global_cache.txt")
        if os.path.exists(gc_path):
            with open(gc_path, 'r', encoding='utf-8') as f:
                return f.read()
    return ""


def extract_chunks(docx_path):
    doc = Document(docx_path)
    return [p.text.strip() for p in doc.paragraphs if p.text.strip()]


def transcribe_metaphor(context, chunk, file_label):
    prompt = (
        f"You are a recursive math translator. Given your prior math knowledge, convert the following symbolic metaphor into a recursive math sequence.\n\n"
        f"--- CONTEXT ---\n{context}\n\n--- METAPHOR ---\n{chunk}\n\nOutput recursive math format:"
    )

    command = [MODEL_PATH, "run", MODEL_NAME]
    process = subprocess.Popen(command, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    stdout_raw, stderr_raw = process.communicate(input=prompt.encode('utf-8'))

    stdout = stdout_raw.decode('utf-8', errors='replace').strip()
    stderr = stderr_raw.decode('utf-8', errors='ignore').strip()

    if not stdout:
        stdout = "[ERROR] Transcription failed."

    return stdout, prompt, stderr


def main():
    context = find_latest_global_cache()

    files = [f for f in os.listdir(INPUT_FOLDER) if f.endswith(".docx")]
    for fname in files:
        path = os.path.join(INPUT_FOLDER, fname)
        chunks = extract_chunks(path)
        base_name = os.path.splitext(fname)[0]

        for i, chunk in enumerate(chunks, start=1):
            print(f"[TRANSCRIBING] {fname} - Chunk {i}/{len(chunks)}")
            output, prompt, stderr = transcribe_metaphor(context, chunk, base_name)
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            chunk_label = f"{base_name}_chunk{i}"
            out_path = os.path.join(EQUATIONS_DIR, f"{chunk_label}.txt")
            with open(out_path, 'w', encoding='utf-8') as f:
                f.write(output)

            append(os.path.join(OUTPUT_DIR, "output.txt"), f"=== {chunk_label} ===\n{output}\n")
            append(os.path.join(LOG_DIR, "log.txt"), f"[{timestamp}] {chunk_label} transcribed.")
            append(os.path.join(CACHE_DIR, "cache.txt"), f"=== {chunk_label} ===\nPrompt SHA256: {hash_content(prompt)}\n{prompt}\n--- Output SHA256: {hash_content(output)} ---\n{output}\n")

    print("=== METAPHOR HARNESS COMPLETE ===")
    print("Session folder:", SESSION_PATH)


if __name__ == "__main__":
    main()
