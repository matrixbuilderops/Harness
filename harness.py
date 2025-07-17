import os
import glob
import time

from . import config as default_config
from .chunk_manager import chunk_blocks, batch_chunks
from .adaptive_controller import AdaptiveController
from .unified_llm_wrapper import get_llm_response
from .jsonl_output import write_jsonl
from .async_logger import AsyncLogger

import glob
import os
from typing import Any, Dict, List, Optional
from multiprocessing import Pool, cpu_count

class Harness:
    """
    A processing harness for running text files through a large language model (LLM).

    This class encapsulates the logic for reading files, chunking them, processing them
    with an LLM, and saving the results. It uses an adaptive controller to adjust
    processing parameters based on system resources.
    """

    def __init__(self, config: Optional[Any] = None) -> None:
        """
        Initializes the Harness.

        Args:
            config: A configuration object. If None, the default config is used.
        """
        self.config = config or default_config
        self.logger = AsyncLogger()
        self.controller = AdaptiveController(
            min_ram=self.config.MIN_RAM,
            max_cpu=self.config.MAX_CPU,
            base_chunk_size=self.config.BASE_CHUNK_SIZE,
            base_processes=self.config.BASE_PROCESSES,
            base_batch_size=self.config.BASE_BATCH_SIZE,
            max_chunk_size=self.config.MAX_CHUNK_SIZE,
            max_processes=self.config.MAX_PROCESSES,
            max_batch_size=self.config.MAX_BATCH_SIZE,
        )

    def process_file(self, filepath: str) -> List[Dict[str, Any]]:
        """
        Processes a single text file.

        Args:
            filepath: The path to the text file.

        Returns:
            A list of dictionaries, where each dictionary contains the input chunk,
            the LLM output, and metadata.
        """
        self.logger.log(f"Processing file: {filepath}")
        with open(filepath, "r", encoding="utf-8") as f:
            text = f.read()

        if self.config.PRE_TOKEN_COUNT > 0:
            text = " ".join(text.split()[self.config.PRE_TOKEN_COUNT :])
        if self.config.POST_TOKEN_COUNT > 0:
            text = " ".join(text.split()[: -self.config.POST_TOKEN_COUNT])

        chunk_size, _, batch_size = self.controller.adjust_parameters()
        chunks = chunk_blocks(text, block_size=chunk_size)
        batches = batch_chunks(chunks, batch_size=batch_size)

        results: List[Dict[str, Any]] = []
        for batch_idx, batch in enumerate(batches):
            self.logger.log(
                f"Processing batch {batch_idx + 1}/{len(batches)} of {os.path.basename(filepath)}"
            )
            batch_results: List[Dict[str, Any]] = []
            for chunk_idx, chunk in enumerate(batch):
                prompt = chunk
                response = get_llm_response(prompt)
                batch_results.append(
                    {
                        "input": chunk,
                        "output": response,
                        "chunk_idx": chunk_idx,
                        "batch_idx": batch_idx,
                    }
                )
                self.logger.log(
                    f"Processed chunk {chunk_idx + 1} in batch {batch_idx + 1}"
                )
            results.extend(batch_results)
            self.logger.log(f"Finished batch {batch_idx + 1}/{len(batches)}")
        return results

    def _process_and_save(self, filepath: str) -> None:
        """Helper function for parallel processing."""
        results = self.process_file(filepath)
        base = os.path.basename(filepath)
        txt_out = f"{base}.llm_output.txt"
        jsonl_out = f"{base}.llm_output.jsonl"

        with open(txt_out, "w", encoding="utf-8") as f:
            for r in results:
                f.write(r["output"].strip() + "\n")

        write_jsonl(results, jsonl_out)
        self.logger.log(f"Wrote outputs for {base}")

    def process_directory(
        self, directory: Optional[str] = None, num_workers: Optional[int] = None
    ) -> None:
        """
        Processes all text files in a directory in parallel.

        Args:
            directory: The directory to process. If None, the directory from the
                       config is used.
            num_workers: The number of worker processes to use. If None, it defaults
                         to the number of CPU cores.
        """
        self.logger.log("Harness started.")
        directory = directory or self.config.DATA_DIR
        data_files = glob.glob(os.path.join(directory, "*"))

        if not num_workers:
            num_workers = cpu_count()

        with Pool(processes=num_workers) as pool:
            pool.map(self._process_and_save, data_files)

        self.logger.log("Harness complete.")
        self.logger.shutdown()