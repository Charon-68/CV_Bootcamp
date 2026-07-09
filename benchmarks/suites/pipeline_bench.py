import asyncio
import time
from typing import Dict, Any
from benchmarks.core.case import BenchmarkCase
from benchmarks.core.result import BenchmarkResult, LatencyMetrics
from benchmarks.profiling.monitor import ResourceMonitor
from runtime.scheduler import PipelineScheduler
from runtime.camera_manager import CameraManager
import logging

logger = logging.getLogger("nexusguard.benchmarks.pipeline")

class PipelineBenchmark(BenchmarkCase):
    """Benchmarks the end-to-end execution pipeline."""
    
    def __init__(self, duration_seconds: int = 10, workers_config: Dict[str, int] = None):
        self.duration = duration_seconds
        self.workers_config = workers_config or {
            "detector": 1,
            "tracker": 1,
            "reasoner": 1,
            "storage": 1
        }
        self.scheduler = None
        self.monitor = ResourceMonitor(sample_interval_seconds=0.5)

    @property
    def name(self) -> str:
        return f"pipeline_{self.duration}s_d{self.workers_config['detector']}_t{self.workers_config['tracker']}"
        
    @property
    def description(self) -> str:
        return f"Benchmarks full async pipeline for {self.duration} seconds."

    def setup(self) -> None:
        # We need a minimal pipeline setup.
        from runtime.frame_queue import FrameQueue
        from runtime.camera_manager import CameraManager
        from runtime.worker_pool import DetectorPool, TrackingPool, ReasoningPool, StoragePool
        from vision.detectors.factory import DetectorFactory
        from vision.trackers.factory import TrackerFactory
        from reasoning.adjudicator import Adjudicator
        
        q_frame = FrameQueue(max_size=100)
        q_detect = FrameQueue(max_size=100)
        q_track = FrameQueue(max_size=100)
        q_reason = FrameQueue(max_size=100)
        
        cm = CameraManager(output_queue=q_frame)
        cm.register_camera("bench_cam_1", "mock", {"width": 640, "height": 480, "fps": 30})
        
        detector = DetectorFactory.create("mock")
        tracker = TrackerFactory.create("mock")
        adjudicator = Adjudicator()
        
        det_pool = DetectorPool(detector, q_frame, q_detect, worker_count=self.workers_config["detector"])
        track_pool = TrackingPool(tracker, q_detect, q_track, worker_count=self.workers_config["tracker"])
        reason_pool = ReasoningPool(adjudicator, q_track, q_reason, worker_count=self.workers_config["reasoner"])
        
        # Mock storage for bench
        class MockDB:
            def insert_incident(self, i): pass
        class MockWS:
            async def broadcast_incident(self, i): pass
            
        store_pool = StoragePool(MockDB(), MockWS(), q_reason, None, worker_count=self.workers_config["storage"])
        
        from runtime.profiler import PerformanceProfiler
        
        self.scheduler = PipelineScheduler(
            camera_manager=cm,
            detector_pool=det_pool,
            tracking_pool=track_pool,
            reasoning_pool=reason_pool,
            storage_pool=store_pool,
            queues=[q_frame, q_detect, q_track, q_reason]
        )
        self.scheduler.profiler = PerformanceProfiler(
            cm, det_pool, track_pool, reason_pool, store_pool, [q_frame, q_detect, q_track, q_reason]
        )
        
        # Start background monitor
        self.monitor.start()

    def run(self) -> BenchmarkResult:
        # Run pipeline asynchronously for `duration`
        start_time = time.time()
        
        async def _run():
            await self.scheduler.start()
            await asyncio.sleep(self.duration)
            await self.scheduler.stop()
            
        asyncio.run(_run())
        
        duration = time.time() - start_time
        
        # Get metrics from profiler
        report = self.scheduler.profiler.get_report()
        
        overall_fps = report["fps"]["overall"]
        
        # For overall pipeline, latencies are tracked in the reasoner or storage pool
        # In the profiler report, we have stage latencies. Let's aggregate them roughly for E2E
        # In a real system, we'd calculate E2E per-frame. Here we just pull from profiler.
        lat_dict = report["latencies_ms"]
        avg_e2e = lat_dict["detector"]["avg"] + lat_dict["tracker"]["avg"] + lat_dict["reasoner"]["avg"]
        
        latency_metrics = LatencyMetrics(
            avg_ms=avg_e2e,
            # We don't have exact P95 E2E unless we track it end-to-end per frame, 
            # but we can sum the p95s roughly, or just use what we have
            p95_ms=lat_dict["detector"]["p95"] + lat_dict["tracker"]["p95"] + lat_dict["reasoner"]["p95"]
        )
        
        return BenchmarkResult(
            name=self.name,
            description=self.description,
            success=True,
            duration_seconds=duration,
            throughput_fps=overall_fps,
            latency=latency_metrics,
            bottlenecks=report.get("bottlenecks", [])
        )

    def teardown(self) -> None:
        metrics = self.monitor.stop()
        # In a real runner we could attach this to the result later
