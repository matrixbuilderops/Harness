import time
import os
from .harness import Harness

def test_throughput():
    print("=== Starting harness throughput test ===")
    start = time.time()
    harness = Harness()
    harness.process_directory()
    duration = time.time() - start
    print(f"Total harness run time: {duration:.2f} seconds")
    # Optionally: check for output files and print their sizes
    output_files = [f for f in os.listdir('.') if f.endswith('.llm_output.txt') or f.endswith('.llm_output.jsonl')]
    for out in output_files:
        print(f"Output file: {out} | Size: {os.path.getsize(out)/1024:.1f} KB")

def run():
    test_throughput()

if __name__ == "__main__":
    run()