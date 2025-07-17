import json
from typing import List, Dict, Any

def write_jsonl(output_list: List[Dict[str, Any]], output_file: str) -> None:
    """
    Writes a list of dicts to a JSONL (JSON Lines) file.
    Each dict in output_list is written as a line in output_file.
    """
    with open(output_file, "w", encoding="utf-8") as f:
        for item in output_list:
            json.dump(item, f)
            f.write("\n")