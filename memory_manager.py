import json
import os
from typing import List, Dict, Any, Callable, Optional

class MemoryManager:
    def __init__(self, trace_file: str = "memory_trace.json"):
        self.trace_file = trace_file
        self.memory: List[Dict[str, Any]] = []
        self._load_memory()

    def _load_memory(self) -> None:
        if os.path.exists(self.trace_file):
            with open(self.trace_file, "r") as f:
                self.memory = json.load(f)
        else:
            self.memory = []

    def save_memory(self) -> None:
        with open(self.trace_file, "w") as f:
            json.dump(self.memory, f)

    def add_context(self, context_block: Dict[str, Any]) -> None:
        self.memory.append(context_block)
        self.save_memory()

    def auto_recall_context(
        self, num_blocks: int = 1, filter_func: Optional[Callable[[Dict[str, Any]], bool]] = None
    ) -> List[Dict[str, Any]]:
        """
        Recall the last N context blocks, optionally filtered.
        Returns a list of relevant context items for the harness.
        """
        relevant = self.memory
        if filter_func:
            relevant = list(filter(filter_func, relevant))
        if num_blocks > 0:
            return relevant[-num_blocks:]
        return relevant