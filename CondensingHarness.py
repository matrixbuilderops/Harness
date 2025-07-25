import os
from multiprocessing import Pool, cpu_count
from datetime import datetime
import hashlib
import subprocess

UNIQUE_INPUT_DIR = "DeduplicationSessions/latest/unique"
MATH_CACHE_PATH = "MathSessions/latest/global_cache.txt"
SESSION_ROOT = "CondensingSessions"
SESSION_PATH = os.path.join(SESSION_ROOT, datetime.now().strftime("%Y-%m-%d_%H-%M-%S"))
OUTPUT_DIR = os.path.join(SESSION_PATH, "condensed")
MODEL_PATH = "/usr/local/bin/ollama"
MODEL_NAME = "mixtral:8x7b-instruct-v0.1-q6_K"

PROMPT = (
    "You are a recursive synthesis engine trained to distill multiple versions of logic into the optimal singular expression."
    " Given the following code samples and prior recursive math cache, create the best unified version of each file."
)


def read_math_cache():
    with open(MATH_CACHE_PATH, 'r', encoding='utf-8') as f:
        return f.read()


def group_similar_files():
    # For simplicity, assume filenames with common prefixes are versions of the same file
    files = sorted(os.listdir(UNIQUE_INPUT_DIR))
    grouped = {}
    for f in files:
        prefix = f.split("_")[0]
        grouped.setdefault(prefix, []).append(f)
    return grouped


def hash_content(text):
    return hashlib.sha256(text.encode('utf-8')).hexdigest()


def condense_group(group_key, files):
    input_texts = []
    for f in files:
        with open(os.path.join(UNIQUE_INPUT_DIR, f), 'r', encoding='utf-8') as file:
            input_texts.append(file.read())
    
    full_input = PROMPT + "\n\n" + read_math_cache() + "\n\nFILES:\n" + "\n\n".join(input_texts)
    command = [MODEL_PATH, "run", MODEL_NAME]
    process = subprocess.Popen(command, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    stdout, stderr = process.communicate(input=full_input.encode('utf-8'))
    
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    output_path = os.path.join(OUTPUT_DIR, f"{group_key}_condensed.qtl")
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(stdout.decode('utf-8', errors='replace'))


def main():
    os.makedirs(SESSION_PATH, exist_ok=True)
    groups = group_similar_files()
    with Pool(cpu_count()) as pool:
        pool.starmap(condense_group, groups.items())
    print(f"Condensing complete. Results in {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
