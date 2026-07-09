from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional
import time

@dataclass
class ResourceMetrics:
    cpu_percent_avg: float = 0.0
    cpu_percent_max: float = 0.0
    memory_mb_avg: float = 0.0
    memory_mb_max: float = 0.0
    gpu_util_avg: float = 0.0
    gpu_util_max: float = 0.0
    network_tx_mb: float = 0.0
    network_rx_mb: float = 0.0

@dataclass
class LatencyMetrics:
    p50_ms: float = 0.0
    p90_ms: float = 0.0
    p95_ms: float = 0.0
    p99_ms: float = 0.0
    avg_ms: float = 0.0
    min_ms: float = 0.0
    max_ms: float = 0.0

@dataclass
class BenchmarkResult:
    name: str
    description: str
    success: bool
    duration_seconds: float
    throughput_fps: float = 0.0
    latency: LatencyMetrics = field(default_factory=LatencyMetrics)
    resources: ResourceMetrics = field(default_factory=ResourceMetrics)
    bottlenecks: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)
    error_message: Optional[str] = None
    timestamp: float = field(default_factory=time.time)

@dataclass
class BenchmarkReport:
    suite_name: str
    total_duration_seconds: float
    results: List[BenchmarkResult] = field(default_factory=list)
    timestamp: float = field(default_factory=time.time)
    system_info: Dict[str, Any] = field(default_factory=dict)
