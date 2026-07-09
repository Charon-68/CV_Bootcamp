import os
from datetime import datetime
from benchmarks.core.result import BenchmarkReport
from benchmarks.reporting.advisor import OptimizationAdvisor

class ReportGenerator:
    """Generates Markdown reports from Benchmark Reports."""

    @staticmethod
    def generate_markdown(report: BenchmarkReport, output_file: str) -> None:
        lines = []
        
        # Header
        lines.append(f"# Performance Benchmark Report: {report.suite_name}")
        lines.append(f"**Date:** {datetime.fromtimestamp(report.timestamp).isoformat()}")
        lines.append(f"**Total Duration:** {report.total_duration_seconds:.2f}s")
        lines.append("")
        
        # System Info
        lines.append("## System Environment")
        for k, v in report.system_info.items():
            lines.append(f"- **{k}**: {v}")
        lines.append("")
        
        # Results Table
        lines.append("## Summary Results")
        lines.append("| Benchmark | Status | FPS | Avg Latency (ms) | P95 Latency (ms) | Max RAM (MB) | Avg CPU (%) |")
        lines.append("|-----------|--------|-----|------------------|------------------|--------------|-------------|")
        
        for res in report.results:
            status = "✅ PASS" if res.success else "❌ FAIL"
            lines.append(f"| {res.name} | {status} | {res.throughput_fps:.2f} | {res.latency.avg_ms:.2f} | {res.latency.p95_ms:.2f} | {res.resources.memory_mb_max:.2f} | {res.resources.cpu_percent_avg:.2f} |")
        
        lines.append("")
        
        # Detailed Results & Recommendations
        lines.append("## Detailed Analysis & Recommendations")
        
        for res in report.results:
            lines.append(f"### {res.name}")
            lines.append(f"_{res.description}_")
            if not res.success:
                lines.append(f"**Error:** {res.error_message}")
                lines.append("")
                continue
                
            if res.bottlenecks:
                lines.append("**Detected Bottlenecks:**")
                for b in res.bottlenecks:
                    lines.append(f"- {b}")
                lines.append("")
                
            suggestions = OptimizationAdvisor.analyze(res)
            lines.append("**Optimization Suggestions:**")
            for s in suggestions:
                lines.append(f"- {s}")
            lines.append("")
            
        # Write to file
        with open(output_file, 'w') as f:
            f.write("\n".join(lines))
