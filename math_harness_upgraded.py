import os
import re
import asyncio
import datetime
import zipfile
import aiofiles
import platform
from typing import List
from pathlib import Path

# Constants
USE_API = False  # Set to True to use API instead of subprocess
ROOT_DIR = Path(__file__).resolve().parent
EQUATION_DIR = ROOT_DIR / "MathEquations"
OUTPUT_ROOT = ROOT_DIR / "MathSessions" / datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
LOG_DIR = OUTPUT_ROOT / "logs"
CACHE_DIR = OUTPUT_ROOT / "cache"
OUT_DIR = OUTPUT_ROOT / "output"
GLOBAL_CACHE_PATH = OUTPUT_ROOT / "global_cache.txt"

REQUIRED_GUIDE = "Math_User_Guide.docx"

# Ensure directories exist
for directory in [LOG_DIR, CACHE_DIR, OUT_DIR]:
    directory.mkdir(parents=True, exist_ok=True)

# Terminal output control
class TerminalProgress:
    def __init__(self):
        self.last_line_len = 0

    def update(self, message: str):
        print("\r" + message.ljust(self.last_line_len), end="")
        self.last_line_len = len(message)

    def newline(self):
        print()
        self.last_line_len = 0

progress = TerminalProgress()

# Sorting logic for .docx files
def sort_docx_files(files: List[Path]) -> List[Path]:
    guide = [f for f in files if REQUIRED_GUIDE.lower() in f.name.lower()]
    level_files = sorted(
        [f for f in files if re.match(r"Math_Levels\s*\d{4}-\d{4}\.docx", f.name)],
        key=lambda x: int(re.findall(r"\d{4}", x.name)[0])
    )
    rest = sorted(set(files) - set(guide) - set(level_files))
    return guide + level_files + rest

# Chunking simulation
def chunk_document(doc_path: Path) -> List[str]:
    # Simulated chunking
    with open(doc_path, 'rb') as f:
        data = f.read()
    size = max(1000, len(data) // 30)
    return [data[i:i+size].decode(errors='ignore') for i in range(0, len(data), size)]

# Save outputs
def save_to_output(doc_name: str, content: str, chunk_idx: int):
    output_path = OUT_DIR / f"{doc_name}_chunk_{chunk_idx}.txt"
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(content)

    cache_path = CACHE_DIR / f"{doc_name}_chunk_{chunk_idx}.cache"
    with open(cache_path, 'w', encoding='utf-8') as f:
        f.write(content)

    with open(GLOBAL_CACHE_PATH, 'a', encoding='utf-8') as f:
        f.write(f"{doc_name}_chunk_{chunk_idx}:\n{content}\n\n")

# Process a chunk with live progress
async def process_chunk(stage: str, chunk_id: int, total: int, file_name: str, content: str):
    pct = int(((chunk_id + 1) / total) * 100)
    progress.update(f"{file_name} — {stage} Chunk {chunk_id+1}/{total} — {pct}%")
    await asyncio.sleep(0.01)  # Simulate async work
    save_to_output(file_name, content, chunk_id)
    progress.newline()

# Full document processing loop
async def process_file(doc_path: Path, index: int, total_files: int):
    file_name = doc_path.stem
    progress.update(f"Processing {file_name} ({index+1}/{total_files})")
    progress.newline()

    chunks = chunk_document(doc_path)
    pre_chunks = chunks[:2]
    post_chunks = chunks[-2:] if len(chunks) > 2 else []
    main_chunks = chunks[2:-2] if len(chunks) > 4 else []

    for stage, stage_chunks in zip(
        ["Pre", "Main", "Post"], [pre_chunks, main_chunks, post_chunks]
    ):
        for i, chunk in enumerate(stage_chunks):
            await process_chunk(stage, i, len(stage_chunks), file_name, chunk)

# Main orchestration
async def main():
    docx_files = list(EQUATION_DIR.glob("*.docx"))
    if not docx_files:
        raise FileNotFoundError("No .docx files found in MathEquations")

    sorted_files = sort_docx_files(docx_files)
    total = len(sorted_files)

    for idx, doc in enumerate(sorted_files):
        await process_file(doc, idx, total)

if __name__ == "__main__":
    asyncio.run(main())
