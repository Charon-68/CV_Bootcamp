import asyncio
import time
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, Callable
from runtime.events import (
    FrameContext,
    WorkerStarted,
    WorkerStopped,
    WorkerRestarted,
    DetectionCompleted,
    TrackingCompleted,
    ReasoningCompleted,
    StorageCompleted,
)
from runtime.logger import get_logger

logger = get_logger("nexusguard.runtime.worker_pool")

class BaseWorkerPool(ABC):
    """Abstract Base Class for all stage-specific Asynchronous Worker Pools."""

    def __init__(
        self,
        stage_name: str,
        input_queue: Any,
        output_queue: Optional[Any],
        worker_count: int = 1,
        event_handler: Optional[Callable[[Any], None]] = None,
        config: Dict[str, Any] = None,
    ):
        self.stage_name = stage_name
        self.input_queue = input_queue
        self.output_queue = output_queue
        self.worker_count = worker_count
        self.event_handler = event_handler
        self.config = config or {}
        
        self.tasks: List[asyncio.Task] = []
        self.running = False
        self.restart_counts = 0
        self.error_counts = 0
        self.processed_count = 0
        self.total_processing_time = 0.0
        
        # Bounded history for percentile calculations
        from collections import deque
        self.latency_history = deque(maxlen=1000)

        # Worker status list
        self.worker_states: Dict[int, str] = {}  # worker_idx -> 'Healthy', 'Failed', 'Idle'

    async def start(self) -> None:
        """Start all worker tasks in the pool."""
        self.running = True
        for i in range(self.worker_count):
            self.worker_states[i] = "Healthy"
            self.tasks.append(asyncio.create_task(self._worker_loop(i)))
            if self.event_handler:
                self.event_handler(WorkerStarted(worker_id=f"{self.stage_name}-{i}", stage=self.stage_name))
        logger.info(f"WorkerPool '{self.stage_name}' started with {self.worker_count} workers.")

    async def stop(self) -> None:
        """Gracefully shut down all workers in the pool."""
        self.running = False
        for task in self.tasks:
            task.cancel()
        
        if self.tasks:
            await asyncio.gather(*self.tasks, return_exceptions=True)
            self.tasks.clear()

        for i in list(self.worker_states.keys()):
            self.worker_states[i] = "Idle"
            if self.event_handler:
                self.event_handler(WorkerStopped(worker_id=f"{self.stage_name}-{i}", stage=self.stage_name))
        logger.info(f"WorkerPool '{self.stage_name}' stopped.")

    async def _worker_loop(self, worker_idx: int) -> None:
        """Central loop for a single worker task with auto-restart and error isolation."""
        worker_id = f"{self.stage_name}-{worker_idx}"
        
        while self.running:
            try:
                # Read next package from input queue
                data = await self.input_queue.get()
                
                # Check for shutdown signal
                if data is None:
                    # Propagate poison pill to downstream if needed and exit
                    if self.output_queue:
                        await self.output_queue.put(None)
                    break

                # Resolve or construct FrameContext
                context: FrameContext
                if isinstance(data, FrameContext):
                    context = data
                else:
                    # Construct Context wrapper from Ingest raw frame payload
                    context = FrameContext(
                        frame_id=data["frame"].index,
                        camera_id=data["camera_id"],
                        timestamp=data["timestamp"],
                        sequence_number=data["sequence_number"],
                        source=data["frame"].source,
                        frame_data=data["frame"],
                    )

                self.worker_states[worker_idx] = "Busy"
                start_time = context.start_timing()

                # Process payload
                processed_context = await self._process(context, worker_idx)
                
                context.record_stage(self.stage_name, start_time)
                
                latency = time.time() - start_time
                self.processed_count += 1
                self.total_processing_time += latency
                self.latency_history.append(latency)

                self.worker_states[worker_idx] = "Healthy"

                # Push to downstream queue
                if self.output_queue and processed_context:
                    await self.output_queue.put(processed_context)

            except asyncio.CancelledError:
                break
            except Exception as e:
                self.error_counts += 1
                self.worker_states[worker_idx] = "Failed"
                logger.error(f"Worker '{worker_id}' encountered error: {e}", exc_info=True)
                
                if self.event_handler:
                    self.event_handler(WorkerRestarted(
                        worker_id=worker_id,
                        stage=self.stage_name,
                        reason=str(e)
                    ))
                
                self.restart_counts += 1
                await asyncio.sleep(1.0)  # cool-off

    @abstractmethod
    async def _process(self, context: FrameContext, worker_idx: int) -> Optional[FrameContext]:
        """Perform the actual processing on the FrameContext."""
        pass

    def get_stats(self) -> Dict[str, Any]:
        avg_processing_time = (
            self.total_processing_time / self.processed_count
            if self.processed_count > 0 else 0.0
        )
        idle_count = sum(1 for state in self.worker_states.values() if state in ("Healthy", "Idle"))
        active_count = len(self.worker_states) - idle_count
        
        # Calculate percentiles
        latencies = sorted(self.latency_history)
        n = len(latencies)
        p50 = latencies[int(n * 0.5)] if n > 0 else 0.0
        p90 = latencies[int(n * 0.9)] if n > 0 else 0.0
        p95 = latencies[int(n * 0.95)] if n > 0 else 0.0
        p99 = latencies[int(n * 0.99)] if n > 0 else 0.0
        
        return {
            "processed_count": self.processed_count,
            "average_processing_time_ms": avg_processing_time * 1000,
            "p50_ms": p50 * 1000,
            "p90_ms": p90 * 1000,
            "p95_ms": p95 * 1000,
            "p99_ms": p99 * 1000,
            "error_count": self.error_counts,
            "restart_count": self.restart_counts,
            "active_workers": active_count,
            "idle_workers": idle_count,
        }


# --- Concrete Pipeline Stage Worker Pools ---

class DetectorPool(BaseWorkerPool):
    def __init__(self, detector: Any, *args, **kwargs):
        super().__init__("detector", *args, **kwargs)
        self.detector = detector

    async def _process(self, context: FrameContext, worker_idx: int) -> Optional[FrameContext]:
        # Run detection using injected BaseDetector
        normalized_frame = context.frame_data
        # Make it run in executor if it blocks, but since we are using asyncio, mock is async-friendly
        result = self.detector.detect(normalized_frame)
        context.detections = result.detections
        
        if self.event_handler:
            self.event_handler(DetectionCompleted(
                frame_id=context.frame_id,
                camera_id=context.camera_id,
                latency_ms=(time.time() - context.timestamp) * 1000
            ))
        return context


class TrackingPool(BaseWorkerPool):
    def __init__(self, tracker: Any, *args, **kwargs):
        super().__init__("tracker", *args, **kwargs)
        self.tracker = tracker

    async def _process(self, context: FrameContext, worker_idx: int) -> Optional[FrameContext]:
        # Run tracking update
        track_result = self.tracker.update(context.detections, context.frame_id)
        context.tracking_result = track_result
        
        if self.event_handler:
            self.event_handler(TrackingCompleted(
                frame_id=context.frame_id,
                camera_id=context.camera_id,
                latency_ms=(time.time() - context.timestamp) * 1000
            ))
        return context


class ReasoningPool(BaseWorkerPool):
    def __init__(self, adjudicator: Any, *args, **kwargs):
        super().__init__("reasoner", *args, **kwargs)
        self.adjudicator = adjudicator

    async def _process(self, context: FrameContext, worker_idx: int) -> Optional[FrameContext]:
        # Perform Reasoning/Adjudication
        # Reconstruct verified objects from detections
        from vision.types import VerifiedObjects
        verified = VerifiedObjects(
            frame_index=context.frame_id,
            items=context.detections,
        )
        
        decision = self.adjudicator.decide(verified, {"camera_id": context.camera_id})
        context.incident = decision.event
        
        if self.event_handler:
            self.event_handler(ReasoningCompleted(
                frame_id=context.frame_id,
                camera_id=context.camera_id,
                latency_ms=(time.time() - context.timestamp) * 1000
            ))
        return context


class StoragePool(BaseWorkerPool):
    def __init__(self, database: Any, broadcast_manager: Any, *args, **kwargs):
        super().__init__("storage", *args, **kwargs)
        self.database = database
        self.broadcast_manager = broadcast_manager

    async def _process(self, context: FrameContext, worker_idx: int) -> Optional[FrameContext]:
        # Persist to database (SQLite)
        if self.database and context.incident:
            self.database.insert_incident(context.incident)
        
        # Broadcast to Websockets
        if self.broadcast_manager and context.incident:
            # Broadcast on event bus
            event_payload = {
                "frame_index": context.incident.frame_index,
                "risk": context.incident.risk,
                "label": context.incident.label,
                "summary": context.incident.summary,
                "camera_id": context.camera_id,
            }
            await self.broadcast_manager.broadcast_incident(event_payload)
            
        if self.event_handler:
            self.event_handler(StorageCompleted(
                frame_id=context.frame_id,
                camera_id=context.camera_id,
                latency_ms=(time.time() - context.timestamp) * 1000
            ))
        return context
