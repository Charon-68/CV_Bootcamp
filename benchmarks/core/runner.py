import time
import platform
import psutil
from typing import List, Dict, Any
from benchmarks.core.case import BenchmarkCase
from benchmarks.core.result import BenchmarkResult, BenchmarkReport
import logging

logger = logging.getLogger("nexusguard.benchmarks")

class BenchmarkSuite:
    """A collection of BenchmarkCases."""
    
    def __init__(self, name: str):
        self.name = name
        self.cases: List[BenchmarkCase] = []

    def add_case(self, case: BenchmarkCase) -> None:
        """Add a benchmark case to the suite."""
        self.cases.append(case)

class BenchmarkRunner:
    """Orchestrates the execution of a BenchmarkSuite and generates reports."""
    
    @staticmethod
    def _get_system_info() -> Dict[str, Any]:
        """Gather basic system information."""
        return {
            "os": platform.system(),
            "os_release": platform.release(),
            "architecture": platform.machine(),
            "cpu_cores": psutil.cpu_count(logical=False),
            "logical_cpus": psutil.cpu_count(logical=True),
            "total_ram_gb": round(psutil.virtual_memory().total / (1024**3), 2),
            "python_version": platform.python_version()
        }

    def run_suite(self, suite: BenchmarkSuite) -> BenchmarkReport:
        """Run all cases in a suite sequentially."""
        logger.info(f"Starting Benchmark Suite: {suite.name}")
        start_time = time.time()
        results: List[BenchmarkResult] = []

        for case in suite.cases:
            result = case.execute()
            results.append(result)

        total_duration = time.time() - start_time
        
        report = BenchmarkReport(
            suite_name=suite.name,
            total_duration_seconds=total_duration,
            results=results,
            system_info=self._get_system_info()
        )
        
        logger.info(f"Finished Benchmark Suite: {suite.name} in {total_duration:.2f}s")
        return report
