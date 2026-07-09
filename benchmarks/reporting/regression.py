from typing import List
from benchmarks.core.result import BenchmarkReport

class RegressionDetector:
    """Detects performance regressions between two benchmark runs."""

    @staticmethod
    def compare(baseline: BenchmarkReport, current: BenchmarkReport) -> List[str]:
        regressions = []
        
        baseline_results = {r.name: r for r in baseline.results if r.success}
        
        for current_res in current.results:
            if not current_res.success:
                continue
                
            if current_res.name in baseline_results:
                base_res = baseline_results[current_res.name]
                
                # Throughput regression (>10% drop)
                if base_res.throughput_fps > 0:
                    fps_drop = (base_res.throughput_fps - current_res.throughput_fps) / base_res.throughput_fps
                    if fps_drop > 0.10:
                        regressions.append(f"[{current_res.name}] FPS Regression: {base_res.throughput_fps:.2f} -> {current_res.throughput_fps:.2f} (-{fps_drop*100:.1f}%)")
                
                # Latency regression (>10% increase)
                if base_res.latency.avg_ms > 0:
                    lat_inc = (current_res.latency.avg_ms - base_res.latency.avg_ms) / base_res.latency.avg_ms
                    if lat_inc > 0.10:
                        regressions.append(f"[{current_res.name}] Latency Regression (Avg): {base_res.latency.avg_ms:.2f}ms -> {current_res.latency.avg_ms:.2f}ms (+{lat_inc*100:.1f}%)")
                        
                if base_res.latency.p95_ms > 0:
                    p95_inc = (current_res.latency.p95_ms - base_res.latency.p95_ms) / base_res.latency.p95_ms
                    if p95_inc > 0.10:
                        regressions.append(f"[{current_res.name}] Latency Regression (P95): {base_res.latency.p95_ms:.2f}ms -> {current_res.latency.p95_ms:.2f}ms (+{p95_inc*100:.1f}%)")

                # Memory regression (>10% increase)
                if base_res.resources.memory_mb_max > 0:
                    mem_inc = (current_res.resources.memory_mb_max - base_res.resources.memory_mb_max) / base_res.resources.memory_mb_max
                    if mem_inc > 0.10:
                        regressions.append(f"[{current_res.name}] Memory Regression: {base_res.resources.memory_mb_max:.2f}MB -> {current_res.resources.memory_mb_max:.2f}MB (+{mem_inc*100:.1f}%)")
        
        return regressions
