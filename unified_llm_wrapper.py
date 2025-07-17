import os
from typing import Optional

try:
    import requests
except ImportError:
    requests = None

LLM_MODE = os.getenv("LLM_MODE", "server")  # "server" or "local"
LLM_SERVER_URL = os.getenv("LLM_SERVER_URL", "http://localhost:8000/generate")
MODEL_PATH = os.getenv("LLM_MODEL_PATH", "Mixtral-8x7B-Instruct-v0.1.Q6_K.gguf")
N_THREADS = int(os.getenv("LLM_THREADS", "8"))
N_CTX = int(os.getenv("LLM_CTX", "4096"))

_llm_cache = {}

def get_llm_response(
    prompt: str,
    model: Optional[str] = None,
    n_threads: Optional[int] = None,
    n_ctx: Optional[int] = None,
) -> str:
    """
    Unified LLM client interface.

    This function can operate in two modes, determined by the LLM_MODE environment variable:
    - "server": Sends the prompt to a remote LLM server.
    - "local": Loads a local GGUF model and runs inference directly.

    Args:
        prompt: The text prompt to send to the LLM.
        model: The path or name of the model to use. Overrides the default.
        n_threads: The number of threads to use for inference. Overrides the default.
        n_ctx: The context size to use for inference. Overrides the default.

    Returns:
        The LLM's response as a string.

    Raises:
        ImportError: If a required library is not installed for the selected mode.
        ValueError: If an unknown LLM_MODE is set.
        requests.exceptions.RequestException: If there is an error communicating with the server.
    """
    if LLM_MODE == "server":
        if not requests:
            raise ImportError("requests library is required for server mode")
        payload = {
            "prompt": prompt,
            "model": model or MODEL_PATH,
            "n_threads": n_threads or N_THREADS,
            "n_ctx": n_ctx or N_CTX,
        }
        try:
            response = requests.post(LLM_SERVER_URL, json=payload, timeout=180)
            response.raise_for_status()
            return response.json().get("response", "")
        except requests.exceptions.RequestException as e:
            print(f"Error communicating with LLM server: {e}")
            return ""
    elif LLM_MODE == "local":
        try:
            from llama_cpp import Llama
        except ImportError:
            raise ImportError("llama-cpp-python is required for local mode")

        model_path = model or MODEL_PATH
        if model_path in _llm_cache:
            llm = _llm_cache[model_path]
        else:
            try:
                llm = Llama(
                    model_path=model_path,
                    n_ctx=n_ctx or N_CTX,
                    n_threads=n_threads or N_THREADS,
                    verbose=False,
                )
                _llm_cache[model_path] = llm
            except Exception as e:
                print(f"Error loading local LLM model: {e}")
                return ""
        try:
            result = llm(prompt=prompt, max_tokens=512, stop=["</s>"])
            return result["choices"][0]["text"]
        except Exception as e:
            print(f"Error during local LLM inference: {e}")
            return ""
    else:
        raise ValueError(f"Unknown LLM_MODE: {LLM_MODE}")