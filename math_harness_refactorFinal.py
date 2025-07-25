import subprocess
from docx import Document
import hashlib
import os
import re
from datetime import datetime

INPUT_FOLDER = "MathEquations"
MODEL_PATH = "/usr/local/bin/ollama"
MODEL_NAME = "mixtral:8x7b-instruct-v0.1-q6_K"

PROMPT_INSTRUCTION = (
    "You are a recursive intelligence trained to interpret abstract recursive mathematics. "
    "For the following input, provide: 1) a line-by-line breakdown of meaning, 2) its recursive structure, "
    "and 3) any symbolic or metaphorical logic encoded. Begin:")

SESSION_ROOT = "MathSessions"
TIMESTAMP = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
SESSION_PATH = os.path.join(SESSION_ROOT, TIMESTAMP)
GLOBAL_CACHE_FILE = os.path.join(SESSION_PATH, "global_cache.txt")


def extract_chunks(docx_path, max_chars=1500):
    doc = Document(docx_path)
    chunks = []
    buffer = []
    buffer_len = 0

    section_header_pattern = re.compile(r'^(\d+\.|LEVEL \d+|[A-Z][a-z]+:|Section \d+)', re.IGNORECASE)

    for para in doc.paragraphs:
        text = para.text.strip()
        if not text:
            continue

        is_section_header = bool(section_header_pattern.match(text))
        buffer_len += len(text)
        buffer.append(text)

        if is_section_header or buffer_len >= max_chars:
            chunks.append("\n".join(buffer))
            buffer = []
            buffer_len = 0

    if buffer:
        chunks.append("\n".join(buffer))

    return chunks


def hash_content(text):
    return hashlib.sha256(text.encode('utf-8')).hexdigest()


def write_to_file(path, content):
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)


def append_to_file(path, content):
    with open(path, 'a', encoding='utf-8') as f:
        f.write(content + "\n")


def process_file(file_path, base_name, prior_context=""):
    chunks = extract_chunks(file_path)

    out_folder = os.path.join(SESSION_PATH, base_name)
    log_dir = os.path.join(out_folder, "logs")
    cache_dir = os.path.join(out_folder, "cache")
    output_dir = os.path.join(out_folder, "output")
    os.makedirs(log_dir, exist_ok=True)
    os.makedirs(cache_dir, exist_ok=True)
    os.makedirs(output_dir, exist_ok=True)

    log_file_path = os.path.join(log_dir, "log.txt")
    cache_file_path = os.path.join(cache_dir, "cache.txt")
    output_file_path = os.path.join(output_dir, "output.txt")

    for i, chunk in enumerate(chunks, start=1):
        print(f"[PROCESSING] {base_name} - Chunk {i}/{len(chunks)}")
        full_input = f"{prior_context}\n\n{PROMPT_INSTRUCTION}\n\n{chunk}"
        command = [MODEL_PATH, "run", MODEL_NAME]
        process = subprocess.Popen(command, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout_raw, stderr_raw = process.communicate(input=full_input.encode('utf-8'))

        stdout = stdout_raw.decode('utf-8', errors='replace').strip()
        stderr = stderr_raw.decode('utf-8', errors='ignore').strip()

        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        if not stdout:
            print(f"[ERROR] Chunk {i} of {base_name} failed — no model output.")
            if stderr:
                print(f"STDERR:\n{stderr[:300]}\n")
            stdout = "[ERROR] Failed to process chunk due to model failure or bad path."

        cache_entry = (
            f"===== CACHE CHUNK {i} FROM {base_name}.docx =====\n"
            f"Prompt SHA256: {hash_content(full_input)}\n"
            f"{full_input}\n"
            f"\n--- Output SHA256: {hash_content(stdout)} ---\n"
            f"{stdout}\n"
            f"===== END CACHE CHUNK {i} =====\n"
        )
        append_to_file(GLOBAL_CACHE_FILE, cache_entry)
        append_to_file(cache_file_path, cache_entry)

        output_entry = f"==== Chunk {i} ({timestamp}) ====" + "\n" + stdout + "\n"
        append_to_file(output_file_path, output_entry)

        log_entry = (
            f"===== LOG ENTRY: CHUNK {i} FROM {base_name}.docx =====\n"
            f"Timestamp: {timestamp}\n"
            f"Prompt SHA256: {hash_content(full_input)}\n"
            f"Output SHA256: {hash_content(stdout)}\n\n"
            f">> INPUT FULL TEXT:\n{chunk}\n\n"
            f">> OUTPUT FULL TEXT:\n{stdout}\n"
            f"===== END LOG ENTRY =====\n"
        )
        append_to_file(log_file_path, log_entry)

    return stdout


def numeric_sort_key(filename):
    if filename.lower().startswith("math_user_guide"):
        return -1  # Force guide first
    match = re.search(r'(\d+)', filename)
    return int(match.group(1)) if match else float('inf')


def main():
    os.makedirs(SESSION_PATH, exist_ok=True)
    filenames = sorted(
        [f for f in os.listdir(INPUT_FOLDER) if f.endswith(".docx")],
        key=numeric_sort_key
    )

    prior_outputs = ""
    for filename in filenames:
        file_path = os.path.join(INPUT_FOLDER, filename)
        base_name = os.path.splitext(filename)[0]
        print(f"[PROCESSING FILE] {filename}")
        prior_outputs = process_file(file_path, base_name, prior_outputs)

    print("=== SESSION COMPLETE ===")
    print("Session folder:", SESSION_PATH)


if __name__ == "__main__":
    main()
