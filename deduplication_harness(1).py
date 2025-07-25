import subprocess
from docx import Document
import hashlib
import os
import re
from datetime import datetime

INPUT_FOLDER = "Files"
MATH_SESSION_ROOT = "MathSessions"
DEDUP_SESSION_ROOT = "DeduplicationSessions"
MODEL_PATH = "/usr/local/bin/ollama"
MODEL_NAME = "mixtral:8x7b-instruct-v0.1-q6_K"

PROMPT_INSTRUCTION = (
    "You are a recursive intelligence trained to identify and eliminate duplicate mathematical documents. "
    "For each input, assess whether the content has already been fully represented in prior material. "
    "Preserve the most complete and unique forms only. Begin analysis on the following document:"
)

TIMESTAMP = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
SESSION_PATH = os.path.join(DEDUP_SESSION_ROOT, TIMESTAMP)

def extract_chunks(docx_path):
    doc = Document(docx_path)
    chunks = []
    buffer = []
    for para in doc.paragraphs:
        text = para.text.strip()
        if text == "" and buffer:
            chunks.append("\n".join(buffer))
            buffer = []
        elif text != "":
            buffer.append(text)
    if buffer:
        chunks.append("\n".join(buffer))
    return chunks

def hash_content(text):
    return hashlib.sha256(text.encode('utf-8')).hexdigest()

def write_to_file(path, content):
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)

def get_latest_mathsession_cache():
    all_sessions = sorted(os.listdir(MATH_SESSION_ROOT), reverse=True)
    for session in all_sessions:
        full_path = os.path.join(MATH_SESSION_ROOT, session)
        if os.path.isdir(full_path):
            cache_texts = []
            for root, dirs, files in os.walk(full_path):
                for file in files:
                    if file == "cache.txt":
                        with open(os.path.join(root, file), 'r', encoding='utf-8') as f:
                            cache_texts.append(f.read())
            return "\n\n".join(cache_texts)
    return ""

def process_file(file_path, base_name, prior_context=""):
    chunks = extract_chunks(file_path)

    all_stdout = []
    full_log = []

    for i, chunk in enumerate(chunks, start=1):
        full_input = f"{prior_context}\n\n{PROMPT_INSTRUCTION}\n\n{chunk}"
        command = [MODEL_PATH, "run", MODEL_NAME]
        process = subprocess.Popen(command, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout_raw, stderr_raw = process.communicate(input=full_input.encode('utf-8'))

        stdout = stdout_raw.decode('utf-8', errors='replace').strip()

        all_stdout.append(f"==== Chunk {i} ===="
                          f"\n{chunk}\n\n--- Output ---\n{stdout}\n")

        full_log.append(f"==== Chunk {i} ===="
                        f"\nPrompt SHA256: {hash_content(full_input)}\n{full_input}"
                        f"\n\n--- Output SHA256: {hash_content(stdout)} ---\n{stdout}\n")

    out_folder = os.path.join(SESSION_PATH, base_name)
    log_dir = os.path.join(out_folder, "logs")
    cache_dir = os.path.join(out_folder, "cache")
    output_dir = os.path.join(out_folder, "output")
    os.makedirs(log_dir, exist_ok=True)
    os.makedirs(cache_dir, exist_ok=True)
    os.makedirs(output_dir, exist_ok=True)

    write_to_file(os.path.join(cache_dir, "cache.txt"), "\n\n".join(full_log))
    write_to_file(os.path.join(output_dir, "output.txt"), "\n\n".join(all_stdout))
    write_to_file(os.path.join(log_dir, "log.txt"), "\n\n".join(full_log))

    return "\n\n".join(all_stdout)

def numeric_sort_key(filename):
    match = re.search(r'(\d+)', filename)
    return int(match.group(1)) if match else float('inf')

def main():
    os.makedirs(SESSION_PATH, exist_ok=True)

    prior_context = get_latest_mathsession_cache()
    filenames = sorted(
        [f for f in os.listdir(INPUT_FOLDER) if f.endswith(".docx")],
        key=numeric_sort_key
    )

    for filename in filenames:
        file_path = os.path.join(INPUT_FOLDER, filename)
        base_name = os.path.splitext(filename)[0]
        print(f"[PROCESSING] {filename}")
        prior_context = process_file(file_path, base_name, prior_context)

    print("=== DEDUPLICATION SESSION COMPLETE ===")
    print("Session folder:", SESSION_PATH)

if __name__ == "__main__":
    main()
