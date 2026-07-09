import asyncio
import time
from typing import Any, Dict, Optional
from runtime.logger import get_logger

logger = get_logger("nexusguard.runtime.frame_queue")

class FrameQueue:
    """Asynchronous bounded queue for passing Frame objects between stages with statistics and backpressure."""

    def __init__(self, max_size: int = 100, drop_policy: str = "oldest"):
        """
        Args:
            max_size: Bounded size of the queue.
            drop_policy: Strategy when queue overflows ('oldest', 'newest', 'block').
        """
        self.max_size = max_size
        self.drop_policy = drop_policy.lower()
        self._queue = collections_deque = []  # We can use asyncio.Queue or a custom list + lock/Semaphore
        self._condition = asyncio.Condition()
        
        # Telemetry metrics
        self.dropped_frames = 0
        self.peak_size = 0
        self.total_wait_time = 0.0
        self.total_processed = 0

    async def put(self, item: Any, block: bool = True) -> bool:
        """Put an item into the queue.

        Args:
            item: The payload to enqueue.
            block: If True, blocks when drop_policy is 'block'. Otherwise returns False on full.

        Returns:
            bool: True if item was enqueued, False if dropped.
        """
        async with self._condition:
            if len(self._queue) >= self.max_size:
                if self.drop_policy == "block":
                    if not block:
                        self.dropped_frames += 1
                        return False
                    while len(self._queue) >= self.max_size:
                        await self._condition.wait()
                elif self.drop_policy == "oldest":
                    # Remove the oldest item (front of the queue)
                    dropped = self._queue.pop(0)
                    self.dropped_frames += 1
                    logger.debug("FrameQueue overflow: dropped oldest frame")
                elif self.drop_policy == "newest":
                    # Drop the incoming item
                    self.dropped_frames += 1
                    logger.debug("FrameQueue overflow: dropped incoming frame")
                    return False
                else:
                    # Default: drop oldest
                    self._queue.pop(0)
                    self.dropped_frames += 1

            # Put item with enqueue timestamp
            self._queue.append((item, time.time()))
            self.peak_size = max(self.peak_size, len(self._queue))
            self._condition.notify_all()
            return True

    def put_nowait(self, item: Any) -> bool:
        """Non-blocking put, useful for synchronous code."""
        if len(self._queue) >= self.max_size:
            if self.drop_policy == "oldest":
                self._queue.pop(0)
                self.dropped_frames += 1
            elif self.drop_policy == "newest" or self.drop_policy == "block":
                self.dropped_frames += 1
                return False
        
        self._queue.append((item, time.time()))
        self.peak_size = max(self.peak_size, len(self._queue))
        return True

    async def get(self) -> Any:
        """Get an item from the queue, blocking if empty."""
        async with self._condition:
            while not self._queue:
                await self._condition.wait()
            item, put_time = self._queue.pop(0)
            wait_time = time.time() - put_time
            self.total_wait_time += wait_time
            self.total_processed += 1
            self._condition.notify_all()
            return item

    def get_nowait(self) -> Optional[Any]:
        """Non-blocking get. Returns None if empty."""
        if not self._queue:
            return None
        item, put_time = self._queue.pop(0)
        wait_time = time.time() - put_time
        self.total_wait_time += wait_time
        self.total_processed += 1
        return item

    async def clear(self) -> None:
        """Clear all items from the queue."""
        async with self._condition:
            self._queue.clear()
            self._condition.notify_all()

    def qsize(self) -> int:
        """Return the current size of the queue."""
        return len(self._queue)

    def get_metrics(self) -> Dict[str, Any]:
        """Return metric snapshots of the queue."""
        avg_wait = self.total_wait_time / self.total_processed if self.total_processed > 0 else 0.0
        return {
            "queue_length": len(self._queue),
            "dropped_frames": self.dropped_frames,
            "peak_queue_size": self.peak_size,
            "average_wait_time_seconds": avg_wait,
        }
