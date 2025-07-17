import requests
import os
from typing import Optional

LLM_SERVER_URL = os.getenv("LLM_SERVER_URL", "http://localhost:8000/generate")

def get_llm_response(
    prompt: str,
    model: Optional[str] = None,
    n_threads: Optional[int] = None,
    n_ctx: Optional[int] = None,
) -> str:
    """
    Sends a prompt to a local LLM server and returns the generated response.
    Optionally override model, n_threads, and n_ctx per request.
    """
    payload = {
        "prompt": prompt,
    }
    if model:
        payload["model"] = model
    if n_threads:
        payload["n_threads"] = n_threads
    if n_ctx:
        payload["n_ctx"] = n_ctx

    try:
        response = requests.post(LLM_SERVER_URL, json=payload, timeout=180)
        response.raise_for_status()
        return response.json().get("response", "")
    except requests.exceptions.RequestException as e:
        print(f"Error communicating with LLM server: {e}")
        return ""