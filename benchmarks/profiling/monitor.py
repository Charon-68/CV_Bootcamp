import psutil
import threading
import time
from typing import List, Optional
from benchmarks.core.result import ResourceMetrics
import logging

logger = logging.getLogger("nexusguard.benchmarks.monitor")

class ResourceMonitor:
    """Monitors system resources asynchronously during a benchmark run."""
    
    def __init__(self, sample_interval_seconds: float = 0.5):
        self.sample_interval = sample_interval_seconds
        self._stop_event = threading.Event()
        self._thread: Optional[threading.Thread] = None
        
        self.cpu_samples: List[float] = []
        self.memory_samples: List[float] = []
        # Note: GPU monitoring omitted as it requires pynvml/nvidia-smi which might not be cross-platform
        # Could be added later with a conditional import.
        self._initial_net_io = None
        self._final_net_io = None

    def start(self) -> None:
        """Start the background monitoring thread."""
        self.cpu_samples.clear()
        self.memory_samples.clear()
        self._stop_event.clear()
        
        # Initialize net IO counters
        self._initial_net_io = psutil.net_io_counters()
        
        # Initialize CPU percent (first call returns 0.0 usually)
        psutil.cpu_percent(interval=None)

        self._thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self._thread.start()
        logger.debug("ResourceMonitor started.")

    def _monitor_loop(self) -> None:
        while not self._stop_event.is_set():
            try:
                # Sample CPU and Memory
                cpu = psutil.cpu_percent(interval=None)
                mem = psutil.Process().memory_info().rss / (1024 * 1024)
                
                self.cpu_samples.append(cpu)
                self.memory_samples.append(mem)
                
                # Sleep for interval or until stopped
                self._stop_event.wait(self.sample_interval)
            except Exception as e:
                logger.error(f"Error in ResourceMonitor loop: {e}")
                break

    def stop(self) -> ResourceMetrics:
        """Stop monitoring and calculate aggregated metrics."""
        self._stop_event.set()
        if self._thread:
            self._thread.join(timeout=2.0)
        
        self._final_net_io = psutil.net_io_counters()
        
        metrics = ResourceMetrics()
        
        if self.cpu_samples:
            metrics.cpu_percent_avg = sum(self.cpu_samples) / len(self.cpu_samples)
            metrics.cpu_percent_max = max(self.cpu_samples)
            
        if self.memory_samples:
            metrics.memory_mb_avg = sum(self.memory_samples) / len(self.memory_samples)
            metrics.memory_mb_max = max(self.memory_samples)
            
        if self._initial_net_io and self._final_net_io:
            bytes_sent = self._final_net_io.bytes_sent - self._initial_net_io.bytes_sent
            bytes_recv = self._final_net_io.bytes_recv - self._initial_net_io.bytes_recv
            metrics.network_tx_mb = bytes_sent / (1024 * 1024)
            metrics.network_rx_mb = bytes_recv / (1024 * 1024)
            
        logger.debug("ResourceMonitor stopped.")
        return metrics
