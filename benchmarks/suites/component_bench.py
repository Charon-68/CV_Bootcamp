import asyncio
import time
from typing import Dict, Any, List
from benchmarks.core.case import BenchmarkCase
from benchmarks.core.result import BenchmarkResult, LatencyMetrics
from benchmarks.profiling.monitor import ResourceMonitor
from benchmarks.workloads.generator import SyntheticLoadGenerator
from vision.detectors.factory import DetectorFactory
from vision.trackers.factory import TrackerFactory
from reasoning.adjudicator import Adjudicator
import logging

logger = logging.getLogger("nexusguard.benchmarks.component")

class DetectorBenchmark(BenchmarkCase):
    """Benchmarks the object detector in isolation."""
    
    def __init__(self, detector_type: str = "mock", frame_count: int = 100):
        self.detector_type = detector_type
        self.frame_count = frame_count
        self.detector = None
        self.frames = []
        self.monitor = ResourceMonitor(sample_interval_seconds=0.1)

    @property
    def name(self) -> str:
        return f"detector_{self.detector_type}_{self.frame_count}frames"
        
    @property
    def description(self) -> str:
        return f"Benchmarks {self.detector_type} detector with {self.frame_count} frames."

    def setup(self) -> None:
        self.detector = DetectorFactory.create(self.detector_type)
        self.frames = SyntheticLoadGenerator.generate_frames(self.frame_count)
        self.monitor.start()

    def run(self) -> BenchmarkResult:
        start_time = time.time()
        latencies = []
        
        for frame in self.frames:
            t0 = time.time()
            # Assuming detector is synchronous or we use it synchronously here
            result = self.detector.detect(frame)
            t1 = time.time()
            latencies.append((t1 - t0) * 1000)
            
        duration = time.time() - start_time
        fps = self.frame_count / duration if duration > 0 else 0
        
        # Calculate percentiles
        latencies.sort()
        n = len(latencies)
        latency_metrics = LatencyMetrics(
            p50_ms=latencies[int(n * 0.5)] if n > 0 else 0.0,
            p90_ms=latencies[int(n * 0.9)] if n > 0 else 0.0,
            p95_ms=latencies[int(n * 0.95)] if n > 0 else 0.0,
            p99_ms=latencies[int(n * 0.99)] if n > 0 else 0.0,
            avg_ms=sum(latencies)/n if n > 0 else 0.0,
            min_ms=latencies[0] if n > 0 else 0.0,
            max_ms=latencies[-1] if n > 0 else 0.0
        )
        
        return BenchmarkResult(
            name=self.name,
            description=self.description,
            success=True,
            duration_seconds=duration,
            throughput_fps=fps,
            latency=latency_metrics,
        )

    def teardown(self) -> None:
        metrics = self.monitor.stop()
        # In a real scenario we'd attach these metrics to the result, but since run() returns it first,
        # we can just log it or we'd refactor to let teardown modify result.
        # For simplicity, we just stop the monitor here.


class TrackerBenchmark(BenchmarkCase):
    """Benchmarks the object tracker in isolation."""
    
    def __init__(self, tracker_type: str = "mock", frame_count: int = 1000):
        self.tracker_type = tracker_type
        self.frame_count = frame_count
        self.tracker = None
        self.payloads = []
        self.monitor = ResourceMonitor(sample_interval_seconds=0.1)

    @property
    def name(self) -> str:
        return f"tracker_{self.tracker_type}_{self.frame_count}frames"
        
    @property
    def description(self) -> str:
        return f"Benchmarks {self.tracker_type} tracker with {self.frame_count} frames."

    def setup(self) -> None:
        self.tracker = TrackerFactory.create(self.tracker_type)
        self.payloads = SyntheticLoadGenerator.generate_detections(self.frame_count)
        self.monitor.start()

    def run(self) -> BenchmarkResult:
        start_time = time.time()
        latencies = []
        
        for p in self.payloads:
            t0 = time.time()
            result = self.tracker.update(p.items, p.frame_index)
            t1 = time.time()
            latencies.append((t1 - t0) * 1000)
            
        duration = time.time() - start_time
        fps = self.frame_count / duration if duration > 0 else 0
        
        # Calculate percentiles
        latencies.sort()
        n = len(latencies)
        latency_metrics = LatencyMetrics(
            p50_ms=latencies[int(n * 0.5)] if n > 0 else 0.0,
            p90_ms=latencies[int(n * 0.9)] if n > 0 else 0.0,
            p95_ms=latencies[int(n * 0.95)] if n > 0 else 0.0,
            p99_ms=latencies[int(n * 0.99)] if n > 0 else 0.0,
            avg_ms=sum(latencies)/n if n > 0 else 0.0,
            min_ms=latencies[0] if n > 0 else 0.0,
            max_ms=latencies[-1] if n > 0 else 0.0
        )
        
        return BenchmarkResult(
            name=self.name,
            description=self.description,
            success=True,
            duration_seconds=duration,
            throughput_fps=fps,
            latency=latency_metrics,
        )

    def teardown(self) -> None:
        self.monitor.stop()


class ReasonerBenchmark(BenchmarkCase):
    """Benchmarks the adjudicator logic."""
    
    def __init__(self, frame_count: int = 100):
        self.frame_count = frame_count
        self.adjudicator = None
        self.payloads = []
        self.monitor = ResourceMonitor(sample_interval_seconds=0.1)

    @property
    def name(self) -> str:
        return f"reasoner_mock_{self.frame_count}frames"
        
    @property
    def description(self) -> str:
        return f"Benchmarks reasoner with {self.frame_count} verification payloads."

    def setup(self) -> None:
        # Assuming we can mock or use a dummy config
        self.adjudicator = Adjudicator()
        self.payloads = SyntheticLoadGenerator.generate_verified_objects(self.frame_count)
        self.monitor.start()

    def run(self) -> BenchmarkResult:
        start_time = time.time()
        latencies = []
        
        for p in self.payloads:
            t0 = time.time()
            # Adjudicator might be sync or async depending on implementation, assume sync for bench
            result = self.adjudicator.decide(p, {"camera_id": "bench_cam"})
            t1 = time.time()
            latencies.append((t1 - t0) * 1000)
            
        duration = time.time() - start_time
        fps = self.frame_count / duration if duration > 0 else 0
        
        # Calculate percentiles
        latencies.sort()
        n = len(latencies)
        latency_metrics = LatencyMetrics(
            p50_ms=latencies[int(n * 0.5)] if n > 0 else 0.0,
            p90_ms=latencies[int(n * 0.9)] if n > 0 else 0.0,
            p95_ms=latencies[int(n * 0.95)] if n > 0 else 0.0,
            p99_ms=latencies[int(n * 0.99)] if n > 0 else 0.0,
            avg_ms=sum(latencies)/n if n > 0 else 0.0,
            min_ms=latencies[0] if n > 0 else 0.0,
            max_ms=latencies[-1] if n > 0 else 0.0
        )
        
        return BenchmarkResult(
            name=self.name,
            description=self.description,
            success=True,
            duration_seconds=duration,
            throughput_fps=fps,
            latency=latency_metrics,
        )

    def teardown(self) -> None:
        self.monitor.stop()
