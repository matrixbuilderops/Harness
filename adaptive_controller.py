from .resource_monitor import get_system_resources

from typing import Tuple

class AdaptiveController:
    """
    Dynamically adjusts processing parameters based on system resource usage.
    """

    def __init__(
        self,
        min_ram: float = 10.0,
        max_cpu: float = 80.0,
        base_chunk_size: int = 100,
        base_processes: int = 4,
        base_batch_size: int = 10,
        max_chunk_size: int = 512,
        max_processes: int = 16,
        max_batch_size: int = 64,
    ) -> None:
        """
        Initializes the AdaptiveController.

        Args:
            min_ram: The minimum percentage of free RAM to maintain.
            max_cpu: The maximum allowed CPU usage percentage.
            base_chunk_size: The starting chunk size.
            base_processes: The starting number of processes.
            base_batch_size: The starting batch size.
            max_chunk_size: The maximum chunk size.
            max_processes: The maximum number of processes.
            max_batch_size: The maximum batch size.
        """
        self.min_ram = min_ram
        self.max_cpu = max_cpu
        self.base_chunk_size = base_chunk_size
        self.base_processes = base_processes
        self.base_batch_size = base_batch_size
        self.max_chunk_size = max_chunk_size
        self.max_processes = max_processes
        self.max_batch_size = max_batch_size

    def adjust_parameters(self) -> Tuple[int, int, int]:
        """
        Dynamically adjusts chunk size, process count, and batch size.

        Returns:
            A tuple containing the new chunk size, process count, and batch size.
        """
        resources = get_system_resources()
        ram_ok = resources["ram_percent"] < (100 - self.min_ram)
        cpu_ok = resources["cpu_percent"] < self.max_cpu

        if ram_ok:
            chunk_size = min(self.base_chunk_size * 2, self.max_chunk_size)
        else:
            chunk_size = max(self.base_chunk_size // 2, 8)

        if cpu_ok:
            process_count = min(self.base_processes * 2, self.max_processes)
        else:
            process_count = max(1, self.base_processes // 2)

        if ram_ok and cpu_ok:
            batch_size = min(self.base_batch_size * 2, self.max_batch_size)
        else:
            batch_size = max(1, self.base_batch_size // 2)

        return chunk_size, process_count, batch_size