import pytest
import os
from benchmarks.core.runner import BenchmarkRunner, BenchmarkSuite
from benchmarks.core.result import BenchmarkResult
from benchmarks.suites.component_bench import DetectorBenchmark, TrackerBenchmark, ReasonerBenchmark
from benchmarks.suites.pipeline_bench import PipelineBenchmark
from benchmarks.reporting.report import ReportGenerator
from benchmarks.reporting.advisor import OptimizationAdvisor
from benchmarks.reporting.regression import RegressionDetector

def test_benchmark_runner_and_suite():
    suite = BenchmarkSuite("Test Suite")
    
    # We will use short frame counts for tests
    suite.add_case(DetectorBenchmark(detector_type="mock", frame_count=10))
    suite.add_case(TrackerBenchmark(tracker_type="mock", frame_count=10))
    suite.add_case(ReasonerBenchmark(frame_count=5))
    
    runner = BenchmarkRunner()
    report = runner.run_suite(suite)
    
    assert report.suite_name == "Test Suite"
    assert len(report.results) == 3
    for res in report.results:
        assert res.success is True
        assert res.throughput_fps > 0
        assert res.duration_seconds > 0

def test_pipeline_benchmark():
    suite = BenchmarkSuite("Pipeline Suite")
    # Very short duration
    suite.add_case(PipelineBenchmark(duration_seconds=2))
    
    runner = BenchmarkRunner()
    report = runner.run_suite(suite)
    
    assert len(report.results) == 1
    res = report.results[0]
    assert res.success is True
    # The pipeline runs asynchronously, mock pipeline might complete some frames
    # Even if 0 FPS, success should be True
    assert res.duration_seconds >= 1.9

def test_optimization_advisor():
    res = BenchmarkResult(
        name="test",
        description="test",
        success=True,
        duration_seconds=1.0,
        throughput_fps=5.0, # Low FPS -> should trigger advice
        bottlenecks=["Detector is backpressuring"]
    )
    
    advice = OptimizationAdvisor.analyze(res)
    assert len(advice) > 0
    assert any("Increase detector workers" in a for a in advice)
    assert any("Detector is the primary bottleneck" in a for a in advice)

def test_report_generator(tmp_path):
    report_file = tmp_path / "report.md"
    
    suite = BenchmarkSuite("Test")
    suite.add_case(DetectorBenchmark(frame_count=5))
    report = BenchmarkRunner().run_suite(suite)
    
    ReportGenerator.generate_markdown(report, str(report_file))
    
    assert report_file.exists()
    content = report_file.read_text()
    assert "# Performance Benchmark Report: Test" in content
    assert "DetectorBenchmark" in content or "detector_" in content

def test_regression_detector():
    from benchmarks.core.result import LatencyMetrics, ResourceMetrics
    
    base_res = BenchmarkResult(
        name="test_bench",
        description="",
        success=True,
        duration_seconds=1.0,
        throughput_fps=100.0,
        latency=LatencyMetrics(avg_ms=10.0, p95_ms=15.0),
        resources=ResourceMetrics(memory_mb_max=100.0)
    )
    
    # Simulate a run with 20% lower FPS and 50% higher latency
    curr_res = BenchmarkResult(
        name="test_bench",
        description="",
        success=True,
        duration_seconds=1.0,
        throughput_fps=75.0,
        latency=LatencyMetrics(avg_ms=16.0, p95_ms=25.0),
        resources=ResourceMetrics(memory_mb_max=150.0) # 50% higher RAM
    )
    
    from benchmarks.core.result import BenchmarkReport
    base_report = BenchmarkReport(suite_name="b", total_duration_seconds=1.0, results=[base_res])
    curr_report = BenchmarkReport(suite_name="c", total_duration_seconds=1.0, results=[curr_res])
    
    regressions = RegressionDetector.compare(base_report, curr_report)
    
    assert len(regressions) == 4
    assert any("FPS Regression" in r for r in regressions)
    assert any("Latency Regression (Avg)" in r for r in regressions)
    assert any("Latency Regression (P95)" in r for r in regressions)
    assert any("Memory Regression" in r for r in regressions)
