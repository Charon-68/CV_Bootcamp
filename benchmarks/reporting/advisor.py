from benchmarks.core.result import BenchmarkResult
from typing import List

class OptimizationAdvisor:
    """Analyzes benchmark results and provides optimization suggestions."""

    @staticmethod
    def analyze(result: BenchmarkResult) -> List[str]:
        suggestions = []
        
        # Analyze throughput
        if result.throughput_fps > 0 and result.throughput_fps < 15.0:
            suggestions.append("Increase detector workers to improve throughput.")
            suggestions.append("Consider enabling batching in the inference engine.")
            
        # Analyze latency
        if result.latency.avg_ms > 100.0:
            suggestions.append("End-to-end latency is high. Consider using a faster tracker or reducing image resolution.")
        
        # Check bottlenecks reported by the framework
        for bottleneck in result.bottlenecks:
            if "detector" in bottleneck.lower():
                suggestions.append("Detector is the primary bottleneck. Upgrade GPU or switch to a lighter model (e.g., YOLOv8n).")
            elif "tracker" in bottleneck.lower():
                suggestions.append("Tracker is the primary bottleneck. Use a simpler algorithm like SORT instead of DeepSORT.")
            elif "reasoner" in bottleneck.lower():
                suggestions.append("Reasoner is slow. Move reasoner to asynchronous execution or batch requests to the LLM.")
            elif "queue" in bottleneck.lower() and "backpressuring" in bottleneck.lower():
                suggestions.append("Queue backpressure detected. Increase queue size or reduce camera FPS.")
                
        # Analyze resources
        if result.resources.cpu_percent_avg > 80.0:
            suggestions.append("High CPU utilization. Optimize data loading or reduce the number of active cameras.")
            
        if result.resources.memory_mb_max > 4000.0:
            suggestions.append("High Memory usage. Check for memory leaks in worker processes or decrease queue max_size.")

        if not suggestions:
            suggestions.append("No obvious bottlenecks detected. System is running optimally.")
            
        return suggestions
