import time
import psutil
from contextlib import contextmanager


@contextmanager
def profile_resources(process_name: str):
    # Setup
    proc = psutil.Process()

    start_time = time.perf_counter()
    start_cpu = proc.cpu_percent(interval=None)
    start_mem = proc.memory_info().rss / (1024 * 1024)  # MB

    yield  # The endpoint logic runs here

    # Results
    end_time = time.perf_counter()
    duration = end_time - start_time
    cpu_usage = proc.cpu_percent(interval=None)
    end_mem = proc.memory_info().rss / (1024 * 1024)

    print(
        f"Profiling results for pipeline '{process_name}': "
        f"time {duration:.4f}s, "
        f"cpu {cpu_usage}%, "
        f"start ram: {start_mem:.4f}MB, "
        f"end ram: {end_mem:.4fMB}MB"
    )