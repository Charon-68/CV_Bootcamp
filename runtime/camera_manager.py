import asyncio
import time
from typing import Dict, Any, Optional, Callable
from vision.cameras import CameraFactory, BaseCamera
from vision.types import Frame
from runtime.events import FrameCaptured, CameraDisconnected, CameraReconnected
from runtime.logger import get_logger

logger = get_logger("nexusguard.runtime.camera_manager")

class CameraManager:
    """Manages multiple camera ingest streams independently, capturing frames into a central queue."""

    def __init__(self, output_queue: Any, event_handler: Optional[Callable[[Any], None]] = None):
        self.output_queue = output_queue
        self.event_handler = event_handler
        self.cameras: Dict[str, BaseCamera] = {}
        self.camera_configs: Dict[str, Dict[str, Any]] = {}
        self.tasks: Dict[str, asyncio.Task] = {}
        self.states: Dict[str, str] = {}  # camera_id -> 'Healthy', 'Failed', 'Restarting'
        self.running = False

    def register_camera(self, camera_id: str, camera_type: str, config: Dict[str, Any]) -> None:
        """Register a camera configuration."""
        config = config or {}
        config["camera_id"] = camera_id
        self.camera_configs[camera_id] = {
            "type": camera_type,
            "config": config,
        }
        self.states[camera_id] = "Healthy"
        logger.info(f"Registered camera '{camera_id}' (Type: {camera_type})")

    async def start(self) -> None:
        """Start frame ingestion tasks for all registered cameras."""
        self.running = True
        for camera_id in self.camera_configs:
            self.tasks[camera_id] = asyncio.create_task(self._camera_loop(camera_id))
        logger.info("CameraManager started ingestion loops.")

    async def stop(self) -> None:
        """Stop ingestion loops and close all cameras gracefully."""
        self.running = False
        for camera_id, task in self.tasks.items():
            task.cancel()
        
        # Wait for all tasks to cancel
        if self.tasks:
            await asyncio.gather(*self.tasks.values(), return_exceptions=True)
            self.tasks.clear()

        # Close all active camera connections
        for camera_id, camera in list(self.cameras.items()):
            try:
                camera.close()
            except Exception as e:
                logger.error(f"Error closing camera '{camera_id}': {e}")
            del self.cameras[camera_id]
        
        logger.info("CameraManager stopped all ingestion loops.")

    async def _camera_loop(self, camera_id: str) -> None:
        """Independent asynchronous loop for a single camera stream."""
        config_entry = self.camera_configs[camera_id]
        camera_type = config_entry["type"]
        config = config_entry["config"]
        max_fps = config.get("fps", 30)
        delay = 1.0 / max_fps if max_fps > 0 else 0.033

        while self.running:
            camera = None
            try:
                self.states[camera_id] = "Restarting"
                # Instantiate camera source
                camera = CameraFactory.create(camera_type, config)
                self.cameras[camera_id] = camera
                self.states[camera_id] = "Healthy"
                logger.info(f"Connected to camera '{camera_id}'")
                
                if self.event_handler:
                    self.event_handler(CameraReconnected(camera_id=camera_id))

                sequence_number = 0
                while self.running:
                    start_time = time.time()
                    if not camera.is_alive():
                        raise RuntimeError(f"Camera '{camera_id}' stream died.")

                    frame = camera.read()
                    if frame is not None:
                        # Construct standardized Frame Context/Frame metadata
                        frame.source = config.get("source", frame.source)
                        
                        # Pack context payload
                        # Create FrameContext inside the pipeline later or pass here
                        # Push to the output queue (frame_queue)
                        await self.output_queue.put({
                            "camera_id": camera_id,
                            "frame": frame,
                            "sequence_number": sequence_number,
                            "timestamp": time.time(),
                        })

                        if self.event_handler:
                            self.event_handler(FrameCaptured(frame_id=frame.index, camera_id=camera_id))
                        sequence_number += 1

                    # Keep FPS bounded
                    elapsed = time.time() - start_time
                    if elapsed < delay:
                        await asyncio.sleep(delay - elapsed)
                    else:
                        await asyncio.sleep(0.001)

            except asyncio.CancelledError:
                break
            except Exception as e:
                self.states[camera_id] = "Failed"
                logger.error(f"Error in ingestion loop for camera '{camera_id}': {e}")
                if self.event_handler:
                    self.event_handler(CameraDisconnected(camera_id=camera_id, reason=str(e)))
                
                # Cleanup connection and sleep before retry
                if camera:
                    try:
                        camera.close()
                    except Exception:
                        pass
                await asyncio.sleep(5.0)  # Retry cool-off period

    def get_camera_status(self, camera_id: str) -> Dict[str, Any]:
        """Return status and telemetry metrics for a camera."""
        camera = self.cameras.get(camera_id)
        stats = camera.get_stats() if camera else {}
        return {
            "camera_id": camera_id,
            "status": self.states.get(camera_id, "Offline"),
            "fps": stats.get("fps", 0.0),
            "dropped_frames": stats.get("dropped_frames", 0),
            "reconnect_count": stats.get("reconnect_count", 0),
        }
