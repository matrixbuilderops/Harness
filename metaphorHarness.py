import os
from multiprocessing import Pool, cpu_count
from datetime import datetime
import hashlib
import subprocess
from docx import Document

MATH_CACHE_PATH = "MathSessions/latest/global_cache.txt"
METAPHOR_FOLDER = "MathMetaphors"
SESSION_ROOT = "MetaphorSessions"
SESSION_PATH = os.path.join(SESSION_ROOT, datetime.now().strftime("%Y-%m-%d_%H-%M-%S"))
GENERATED_EQUATIONS_PATH = os.path.join(SESSION_PATH, "generated_equations.txt")
MODEL_PATH = "/usr/local/bin/ollama"
MODEL_NAME = "mixtral:8x7b-instruct-v0.1-q6_K"

PROMPT = (
    "You are a recursive mathematician. Convert the following metaphorical description into a complete recursive math framework, adhering to prior styles in the cache."
)


def read_math_cache():
    with open(MATH_CACHE_PATH, 'r', encoding='utf-8') as f:
        return f.read()


def extract_text_from_docx(path):
    doc = Document(path)
    return "\n".join([p.text for p in doc.paragraphs if p.text.strip()])


def hash_content(text):
    return hashlib.sha256(text.encode('utf-8')).hexdigest()


def process_metaphor_file(file_path):
    file_name = os.path.basename(file_path)
    metaphor_text = extract_text_from_docx(file_path)
    full_input = PROMPT + "\n\n" + read_math_cache() + f"\n\nMETAPHOR FILE: {file_name}\n" + metaphor_text

    command = [MODEL_PATH, "run", MODEL_NAME]
    process = subprocess.Popen(command, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    stdout, stderr = process.communicate(input=full_input.encode('utf-8'))

    entry = (
        f"===== GENERATED FROM: {file_name} =====\n"
        f"Input SHA256: {hash_content(full_input)}\n"
        f"Generated Math:\n{stdout.decode('utf-8', errors='replace')}\n"
        f"===== END GENERATED =====\n\n"
    )

    with open(GENERATED_EQUATIONS_PATH, 'a', encoding='utf-8') as output_file:
        output_file.write(entry)


def main():
    os.makedirs(SESSION_PATH, exist_ok=True)
    files_to_process = [os.path.join(METAPHOR_FOLDER, f) for f in os.listdir(METAPHOR_FOLDER) if f.endswith(".docx")]
    with Pool(cpu_count()) as pool:
        pool.map(process_metaphor_file, files_to_process)
    print(f"Metaphor processing complete. Output saved to {GENERATED_EQUATIONS_PATH}")


if __name__ == "__main__":
    main()
