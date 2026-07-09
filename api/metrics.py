from fastapi import APIRouter
from fastapi.responses import PlainTextResponse
import time

router = APIRouter()

class MetricsStore:
    def __init__(self):
        self.incidents_processed = 0
        self.frames_processed = 0
        self.start_time = time.time()
        self.high_risk_incidents = 0

    def record_incident(self, risk: float):
        self.incidents_processed += 1
        if risk > 0.7:
            self.high_risk_incidents += 1

    def record_frame(self):
        self.frames_processed += 1

metrics_store = MetricsStore()

@router.get("/metrics", response_class=PlainTextResponse)
def get_metrics():
    uptime = time.time() - metrics_store.start_time
    output = [
        "# HELP nexusguard_uptime_seconds Uptime of the NexusGuard API",
        "# TYPE nexusguard_uptime_seconds gauge",
        f"nexusguard_uptime_seconds {uptime}",
        "# HELP nexusguard_frames_processed_total Total frames processed",
        "# TYPE nexusguard_frames_processed_total counter",
        f"nexusguard_frames_processed_total {metrics_store.frames_processed}",
        "# HELP nexusguard_incidents_total Total incidents generated",
        "# TYPE nexusguard_incidents_total counter",
        f"nexusguard_incidents_total {metrics_store.incidents_processed}",
        "# HELP nexusguard_high_risk_incidents_total Total high-risk incidents (>0.7)",
        "# TYPE nexusguard_high_risk_incidents_total counter",
        f"nexusguard_high_risk_incidents_total {metrics_store.high_risk_incidents}"
    ]
    return "\n".join(output) + "\n"
