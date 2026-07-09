import pytest
import time
from vision.types import Frame, NormalizedFrame, Detection, BoundingBox
from vision.cameras import CameraFactory, MockCamera
from vision.detectors import DetectorFactory, MockDetector
from vision.trackers import TrackerFactory, MockTracker
from vision.pipeline import VisionPipeline

def test_factories():
    # Test CameraFactory
    camera = CameraFactory.create("mock", {"width": 320, "height": 240})
    assert isinstance(camera, MockCamera)
    assert camera.width == 320
    camera.close()

    # Test DetectorFactory
    detector = DetectorFactory.create("mock", {"mock_detections": [{"label": "cat", "confidence": 0.95, "bbox": (0, 0, 10, 10)}]})
    assert isinstance(detector, MockDetector)
    detector.shutdown()

    # Test TrackerFactory
    tracker = TrackerFactory.create("mock")
    assert isinstance(tracker, MockTracker)
    tracker.shutdown()

def test_detection_result_schema():
    frame = NormalizedFrame(index=1, timestamp=time.time(), width=640, height=480)
    mock_detections = [{"label": "dog", "confidence": 0.99, "bbox": (10.0, 20.0, 30.0, 40.0)}]
    detector = DetectorFactory.create("mock", {"mock_detections": mock_detections})
    
    result = detector.detect(frame)
    assert result.metadata.frame_id == 1
    assert len(result.detections) == 1
    assert result.detections[0].label == "dog"
    assert result.detections[0].confidence == 0.99
    assert result.detections[0].bbox == (10.0, 20.0, 30.0, 40.0)
    assert result.stats.detection_count == 1
    
    bbox = BoundingBox.from_tuple(result.detections[0].bbox)
    assert bbox.x1 == 10.0
    assert bbox.y1 == 20.0
    assert bbox.to_tuple() == (10.0, 20.0, 30.0, 40.0)

def test_pipeline_dependency_injection():
    camera = CameraFactory.create("mock", {"width": 640, "height": 480})
    detector = DetectorFactory.create("mock", {
        "mock_detections": [{"label": "person", "confidence": 0.88, "bbox": (10, 10, 100, 100)}]
    })
    tracker = TrackerFactory.create("mock")

    pipeline = VisionPipeline(camera=camera, detector=detector, tracker=tracker)
    assert pipeline.camera == camera
    assert pipeline.detector == detector
    assert pipeline.tracker == tracker

    result = pipeline.run_once()
    assert result is not None
    assert result["frame"].index == 0
    assert len(result["detection_result"].detections) == 1
    assert result["track_result"] is not None
    assert len(result["track_result"].tracked_objects) == 1
    assert result["track_result"].tracked_objects[0].track_id == 1
