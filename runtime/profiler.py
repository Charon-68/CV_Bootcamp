import time
import psutil
from typing import Dict, Any, List
from runtime.frame_queue import FrameQueue
from runtime.camera_manager import CameraManager
from runtime.worker_pool import BaseWorkerPool

class PerformanceProfiler:
    """Utility class to measure execution speeds, queues, and memory footprint."""

    def __init__(
        self,
        camera_manager: CameraManager,
        detector_pool: BaseWorkerPool,
        tracking_pool: BaseWorkerPool,
        reasoning_pool: BaseWorkerPool,
        storage_pool: BaseWorkerPool,
        queues: List[FrameQueue],
    ):
        self.camera_manager = camera_manager
        self.detector_pool = detector_pool
        self.tracking_pool = tracking_pool
        self.reasoning_pool = reasoning_pool
        self.storage_pool = storage_pool
        self.queues = queues
        self.start_time = time.time()

    def get_report(self) -> Dict[str, Any]:
        """Generate a complete system profiling report."""
        elapsed = time.time() - self.start_time
        
        # Calculate memory footprint
        process = psutil.Process()
        memory_usage_mb = process.memory_info().rss / (1024 * 1024)

        # Get stats from pools
        det_stats = self.detector_pool.get_stats()
        track_stats = self.tracking_pool.get_stats()
        reason_stats = self.reasoning_pool.get_stats()
        store_stats = self.storage_pool.get_stats()

        # Calculate stage FPS
        det_fps = det_stats["processed_count"] / elapsed if elapsed > 0 else 0.0
        track_fps = track_stats["processed_count"] / elapsed if elapsed > 0 else 0.0
        reason_fps = reason_stats["processed_count"] / elapsed if elapsed > 0 else 0.0
        overall_fps = store_stats["processed_count"] / elapsed if elapsed > 0 else 0.0

        # Queue utilization
        queue_metrics = [q.get_metrics() for q in self.queues]
        queue_utilization = [
            round((m["queue_length"] / q.max_size) * 100, 1) if q.max_size > 0 else 0.0
            for q, m in zip(self.queues, queue_metrics)
        ]
        
        bottlenecks = []
        if overall_fps < 10.0:
            bottlenecks.append("Low overall throughput (FPS < 10)")
        
        # Find slowest node by avg processing time
        avg_times = {
            "detector": det_stats["average_processing_time_ms"],
            "tracker": track_stats["average_processing_time_ms"],
            "reasoner": reason_stats["average_processing_time_ms"]
        }
        slowest_node = max(avg_times, key=avg_times.get)
        if avg_times[slowest_node] > 50: # >50ms is slow
            bottlenecks.append(f"Slowest stage is {slowest_node} at {avg_times[slowest_node]:.1f}ms per frame")
            
        for i, util in enumerate(queue_utilization):
            if util > 90.0:
                bottlenecks.append(f"Queue {i} is backpressuring (>{util}% full)")

        return {
            "elapsed_seconds": elapsed,
            "memory_usage_mb": memory_usage_mb,
            "fps": {
                "detector": det_fps,
                "tracker": track_fps,
                "reasoner": reason_fps,
                "overall": overall_fps,
            },
            "latencies_ms": {
                "detector": {
                    "avg": det_stats["average_processing_time_ms"],
                    "p50": det_stats.get("p50_ms", 0.0),
                    "p95": det_stats.get("p95_ms", 0.0),
                    "p99": det_stats.get("p99_ms", 0.0),
                },
                "tracker": {
                    "avg": track_stats["average_processing_time_ms"],
                    "p50": track_stats.get("p50_ms", 0.0),
                    "p95": track_stats.get("p95_ms", 0.0),
                    "p99": track_stats.get("p99_ms", 0.0),
                },
                "reasoner": {
                    "avg": reason_stats["average_processing_time_ms"],
                    "p50": reason_stats.get("p50_ms", 0.0),
                    "p95": reason_stats.get("p95_ms", 0.0),
                    "p99": reason_stats.get("p99_ms", 0.0),
                },
            },
            "queue_utilization_percent": queue_utilization,
            "bottlenecks": bottlenecks
        }
