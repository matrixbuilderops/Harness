# Mixtral Harness

This project is a Python-based harness for processing large amounts of text data with a large language model (LLM). It is designed to be efficient, scalable, and easy to use, both as a standalone script and as a library in other projects.

## Features

- **Adaptive Controller:** Dynamically adjusts processing parameters (chunk size, batch size, etc.) based on system resource usage (CPU and RAM) to maximize throughput.
- **Dual LLM Modes:** Supports two modes for connecting to an LLM:
    - `server` mode: Connects to a running LLM server (e.g., llama.cpp's server).
    - `local` mode: Loads and runs a GGUF model file directly in memory using `llama-cpp-python`.
- **Parallel Processing:** Processes multiple files simultaneously to take full advantage of multi-core CPUs.
- **Model Caching:** Caches the loaded LLM model in memory to avoid reloading it for every request.
- **Batch Processing:** Groups text chunks into batches for more efficient processing.
- **Asynchronous Logging:** Prevents logging from blocking the main processing thread.
- **Importable Library:** The core logic is encapsulated in a `Harness` class, making it easy to import and use in other projects.

## Installation

1.  **Navigate to the project directory:**
    ```bash
    cd MixtralHarness
    ```

2.  **Install the package:**
    ```bash
    pip install .
    ```
    This will install the `mixtral_harness` package and all its dependencies.

## Configuration

The harness is configured using environment variables. You can set these in your shell or create a `.env` file. The main configuration options are in `mixtral_harness/config.py`.

-   `LLM_MODE`: Set to `local` to load a model directly, or `server` to connect to an LLM server.
-   `MODEL_PATH`: The path to your GGUF model file (e.g., `/path/to/your/model.gguf`). This is required for `local` mode.
-   `LLM_SERVER_URL`: The URL of the LLM server (e.g., `http://localhost:8000/generate`). This is required for `server` mode.
-   `DATA_DIR`: The directory containing the text files you want to process.

## Usage

### Standalone Mode

To run the harness as a standalone script, simply run `run.py` from the `MixtralHarness` directory:

```bash
python run.py
```

This will process all the files in the `DATA_DIR` in parallel, using a number of worker processes equal to the number of CPU cores. It will create `.txt` and `.jsonl` output files for each input file.

### Library Mode

To use the harness as a library in your own project, you can import the `Harness` class.

Here's an example:

```python
from mixtral_harness import Harness
from mixtral_harness import config

# Override the default configuration if needed
config.LLM_MODE = "local"
config.MODEL_PATH = "/path/to/your/local/model.gguf"
config.DATA_DIR = "/path/to/your/data"

# Initialize the harness with the custom config
my_harness = Harness(config=config)

# Process a single file
results = my_harness.process_file("/path/to/your/data/some_file.txt")
print(results)

# Or process a whole directory in parallel with 8 worker processes
my_harness.process_directory(num_workers=8)