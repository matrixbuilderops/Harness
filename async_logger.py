import threading
import queue
import time

class AsyncLogger:
    def __init__(self, log_file="harness.log"):
        self.log_file = log_file
        self.log_queue = queue.Queue()
        self.stop_signal = False
        self.thread = threading.Thread(target=self._run)
        self.thread.daemon = True
        self.thread.start()

    def log(self, message):
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        self.log_queue.put(f"[{timestamp}] {message}")

    def _run(self):
        with open(self.log_file, "a", encoding="utf-8") as f:
            while not self.stop_signal or not self.log_queue.empty():
                try:
                    msg = self.log_queue.get(timeout=0.5)
                    f.write(msg + "\n")
                    f.flush()
                except queue.Empty:
                    continue

    def shutdown(self):
        self.stop_signal = True
        self.thread.join()