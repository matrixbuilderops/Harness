import psutil
from typing import Dict

def get_system_resources() -> Dict[str, float]:
    """
    Returns current system RAM and CPU usage as a dict:
    {
        'ram_percent': float (percent of RAM used),
        'cpu_percent': float (percent of CPU used)
    }
    """
    ram_percent = psutil.virtual_memory().percent
    cpu_percent = psutil.cpu_percent(interval=0.5)
    return {
        'ram_percent': ram_percent,
        'cpu_percent': cpu_percent
    }