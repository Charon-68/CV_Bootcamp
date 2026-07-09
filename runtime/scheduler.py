import asyncio
import time
from typing import Dict, Any, List, Optional
from runtime.frame_queue import FrameQueue
from runtime.camera_manager import CameraManager
from runtime.worker_pool import DetectorPool, TrackingPool, ReasoningPool, StoragePool
from runtime.logger import get_logger

logger = get_logger("nexusguard.runtime.scheduler")

class PipelineScheduler:
    """Orchestrates the entire asynchronous pipeline runtime, scheduling and health monitoring."""

    def __init__(
        self,
        camera_manager: CameraManager,
        detector_pool: DetectorPool,
        tracking_pool: TrackingPool,
        reasoning_pool: ReasoningPool,
        storage_pool: StoragePool,
        queues: List[FrameQueue],
    ):
        self.camera_manager = camera_manager
        self.detector_pool = detector_pool
        self.tracking_pool = tracking_pool
        self.reasoning_pool = reasoning_pool
        self.storage_pool = storage_pool
        self.queues = queues
        
        self.running = False
        self.paused = False
        self._monitor_task: Optional[asyncio.Task] = None

    async def start(self) -> None:
        """Start the entire pipeline runtime."""
        if self.running:
            logger.warning("Pipeline is already running.")
            return

        self.running = True
        self.paused = False
        
        # Start pools in reverse dependency order
        await self.storage_pool.start()
        await self.reasoning_pool.start()
        await self.tracking_pool.start()
        await self.detector_pool.start()
        
        # Start cameras last
        await self.camera_manager.start()
        
        # Start runtime monitoring task
        self._monitor_task = asyncio.create_task(self._monitor_loop())
        logger.info("PipelineScheduler successfully started the execution engine.")

    async def stop(self) -> None:
        """Gracefully stop and drain the pipeline."""
        if not self.running:
            return

        self.running = False
        if self._monitor_task:
            self._monitor_task.cancel()
            try:
                await self._monitor_task
            except asyncio.CancelledError:
                pass
            self._monitor_task = None

        # Stop Camera Manager first (no new frames enqueued)
        await self.camera_manager.stop()

        # Shutdown worker pools in order
        await self.detector_pool.stop()
        await self.tracking_pool.stop()
        await self.reasoning_pool.stop()
        await self.storage_pool.stop()

        # Clear remaining items in queues
        for q in self.queues:
            await q.clear()

        logger.info("PipelineScheduler successfully stopped the execution engine.")

    async def pause(self) -> None:
        """Pause frame consumption (by temporarily stopping workers)."""
        if not self.running or self.paused:
            return
        self.paused = True
        logger.info("Pausing pipeline...")
        await self.detector_pool.stop()
        await self.tracking_pool.stop()

    async def resume(self) -> None:
        """Resume frame consumption."""
        if not self.running or not self.paused:
            return
        self.paused = False
        logger.info("Resuming pipeline...")
        await self.detector_pool.start()
        await self.tracking_pool.start()

    async def restart(self) -> None:
        """Restart the entire engine."""
        logger.info("Restarting pipeline scheduler...")
        await self.stop()
        await self.start()

    async def shutdown(self) -> None:
        """Graceful shutdown alias."""
        await self.stop()

    async def _monitor_loop(self) -> None:
        """Background health and queue statistics monitoring loop."""
        while self.running:
            try:
                await asyncio.sleep(5.0)
                
                # Check for queue utilization
                for idx, q in enumerate(self.queues):
                    metrics = q.get_metrics()
                    logger.debug(f"Queue {idx} size: {metrics['queue_length']}/{q.max_size}")

                # Monitor worker health - dynamic restart handled internally in WorkerPools
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in scheduler monitor: {e}")
