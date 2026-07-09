import asyncio
import time
from typing import Dict, Any
from benchmarks.core.case import BenchmarkCase
from benchmarks.core.result import BenchmarkResult, LatencyMetrics
from benchmarks.profiling.monitor import ResourceMonitor
from runtime.scheduler import PipelineScheduler
import logging

logger = logging.getLogger("nexusguard.benchmarks.stress")

class StressBenchmark(BenchmarkCase):
    """Stress tests the pipeline with many cameras."""
    
    def __init__(self, num_cameras: int = 5, duration_seconds: int = 15):
        self.num_cameras = num_cameras
        self.duration = duration_seconds
        self.scheduler = None
        self.monitor = ResourceMonitor(sample_interval_seconds=0.5)

    @property
    def name(self) -> str:
        return f"stress_{self.num_cameras}cams_{self.duration}s"
        
    @property
    def description(self) -> str:
        return f"Stress tests pipeline with {self.num_cameras} mock cameras for {self.duration} seconds."

    def setup(self) -> None:
        from runtime.frame_queue import FrameQueue
        from runtime.camera_manager import CameraManager
        from runtime.worker_pool import DetectorPool, TrackingPool, ReasoningPool, StoragePool
        from vision.detectors.factory import DetectorFactory
        from vision.trackers.factory import TrackerFactory
        from reasoning.adjudicator import Adjudicator
        
        q_frame = FrameQueue(max_size=100, drop_policy="oldest")
        q_detect = FrameQueue(max_size=100, drop_policy="oldest")
        q_track = FrameQueue(max_size=100, drop_policy="oldest")
        q_reason = FrameQueue(max_size=100, drop_policy="oldest")
        
        cm = CameraManager(output_queue=q_frame)
        for i in range(self.num_cameras):
            cm.register_camera(f"cam_{i}", "mock", {"width": 640, "height": 480, "fps": 30})
            
        detector = DetectorFactory.create("mock")
        tracker = TrackerFactory.create("mock")
        adjudicator = Adjudicator()
        
        det_pool = DetectorPool(detector, q_frame, q_detect, worker_count=4)
        track_pool = TrackingPool(tracker, q_detect, q_track, worker_count=2)
        reason_pool = ReasoningPool(adjudicator, q_track, q_reason, worker_count=2)
        
        class MockDB:
            def insert_incident(self, i): pass
        class MockWS:
            async def broadcast_incident(self, i): pass
            
        store_pool = StoragePool(MockDB(), MockWS(), q_reason, None, worker_count=1)
        
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
        self.monitor.start()

    def run(self) -> BenchmarkResult:
        start_time = time.time()
        
        async def _run():
            await self.scheduler.start()
            await asyncio.sleep(self.duration)
            await self.scheduler.stop()
            
        asyncio.run(_run())
        
        duration = time.time() - start_time
        
        report = self.scheduler.profiler.get_report()
        overall_fps = report["fps"]["overall"]
        
        # Calculate rough E2E latency
        lat_dict = report["latencies_ms"]
        avg_e2e = lat_dict["detector"]["avg"] + lat_dict["tracker"]["avg"] + lat_dict["reasoner"]["avg"]
        p95_e2e = lat_dict["detector"]["p95"] + lat_dict["tracker"]["p95"] + lat_dict["reasoner"]["p95"]
        
        latency_metrics = LatencyMetrics(
            avg_ms=avg_e2e,
            p95_ms=p95_e2e
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
        self.monitor.stop()
