import abc
import time
from typing import Dict, Any, Optional
from benchmarks.core.result import BenchmarkResult
import logging

logger = logging.getLogger("nexusguard.benchmarks")

class BenchmarkCase(abc.ABC):
    """Abstract base class for all benchmark tests."""

    @property
    @abc.abstractmethod
    def name(self) -> str:
        """Name of the benchmark."""
        pass

    @property
    @abc.abstractmethod
    def description(self) -> str:
        """Description of what the benchmark tests."""
        pass

    def setup(self) -> None:
        """Prepare the environment before running the benchmark."""
        pass

    def teardown(self) -> None:
        """Clean up the environment after running the benchmark."""
        pass

    @abc.abstractmethod
    def run(self) -> BenchmarkResult:
        """Execute the benchmark and return the results."""
        pass

    def execute(self) -> BenchmarkResult:
        """Orchestrate setup, run, and teardown, handling errors."""
        logger.info(f"Starting benchmark: {self.name}")
        start_time = time.time()
        result = None
        try:
            self.setup()
            result = self.run()
        except Exception as e:
            logger.error(f"Benchmark '{self.name}' failed: {e}", exc_info=True)
            duration = time.time() - start_time
            result = BenchmarkResult(
                name=self.name,
                description=self.description,
                success=False,
                duration_seconds=duration,
                error_message=str(e)
            )
        finally:
            try:
                self.teardown()
            except Exception as e:
                logger.error(f"Teardown for benchmark '{self.name}' failed: {e}", exc_info=True)
        
        logger.info(f"Finished benchmark: {self.name} in {result.duration_seconds:.2f}s")
        return result
