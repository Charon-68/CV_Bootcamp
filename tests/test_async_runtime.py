import asyncio
import pytest
import time
from runtime.frame_queue import FrameQueue
from runtime.camera_manager import CameraManager
from runtime.worker_pool import DetectorPool, TrackingPool, ReasoningPool, StoragePool
from runtime.scheduler import PipelineScheduler
from runtime.events import FrameCaptured, FrameContext
from vision.cameras import MockCamera
from vision.detectors import MockDetector
from vision.trackers import MockTracker
from reasoning import Adjudicator

class MockDB:
    def insert_incident(self, event):
        pass

class MockWS:
    async def broadcast_incident(self, payload):
        pass

@pytest.mark.anyio
async def test_frame_queue_overflow_and_drop_policies():
    # Test 'oldest' drop policy
    q_oldest = FrameQueue(max_size=2, drop_policy="oldest")
    await q_oldest.put("frame_1")
    await q_oldest.put("frame_2")
    # This should drop "frame_1" and keep "frame_2" and "frame_3"
    await q_oldest.put("frame_3")
    
    assert q_oldest.qsize() == 2
    assert await q_oldest.get() == "frame_2"
    assert await q_oldest.get() == "frame_3"

    # Test 'newest' drop policy
    q_newest = FrameQueue(max_size=2, drop_policy="newest")
    await q_newest.put("frame_1")
    await q_newest.put("frame_2")
    # This should drop the incoming "frame_3"
    assert await q_newest.put("frame_3") is False
    assert q_newest.qsize() == 2
    assert await q_newest.get() == "frame_1"
    assert await q_newest.get() == "frame_2"

@pytest.mark.anyio
async def test_camera_manager_and_multiple_cameras():
    q = FrameQueue(max_size=10)
    cm = CameraManager(output_queue=q)
    
    # Register multiple mock cameras
    cm.register_camera("cam_1", "mock", {"width": 320, "height": 240, "fps": 100})
    cm.register_camera("cam_2", "mock", {"width": 640, "height": 480, "fps": 100})
    
    await cm.start()
    # Let ingestion run for a bit
    await asyncio.sleep(0.1)
    await cm.stop()
    
    # Check that both cameras enqueued frames
    assert q.qsize() > 0
    camera_ids = set()
    while q.qsize() > 0:
        item = await q.get()
        camera_ids.add(item["camera_id"])
    
    assert "cam_1" in camera_ids
    assert "cam_2" in camera_ids

@pytest.mark.anyio
async def test_pipeline_scheduler_graceful_shutdown():
    q_frame = FrameQueue(max_size=5)
    q_detect = FrameQueue(max_size=5)
    q_track = FrameQueue(max_size=5)
    q_reason = FrameQueue(max_size=5)

    cm = CameraManager(output_queue=q_frame)
    cm.register_camera("cam_1", "mock", {"fps": 10})

    detector = MockDetector()
    tracker = MockTracker()
    adjudicator = Adjudicator(provider=None)

    db_mock = MockDB()
    ws_mock = MockWS()

    det_pool = DetectorPool(detector, q_frame, q_detect, worker_count=1)
    track_pool = TrackingPool(tracker, q_detect, q_track, worker_count=1)
    reason_pool = ReasoningPool(adjudicator, q_track, q_reason, worker_count=1)
    store_pool = StoragePool(db_mock, ws_mock, q_reason, None, worker_count=1)

    scheduler = PipelineScheduler(
        camera_manager=cm,
        detector_pool=det_pool,
        tracking_pool=track_pool,
        reasoning_pool=reason_pool,
        storage_pool=store_pool,
        queues=[q_frame, q_detect, q_track, q_reason],
    )

    await scheduler.start()
    await asyncio.sleep(0.1)
    await scheduler.stop()

    assert not scheduler.running
    assert q_frame.qsize() == 0
    assert q_detect.qsize() == 0
