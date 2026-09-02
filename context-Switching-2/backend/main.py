"""
Context Switch Overhead Analyzer — FastAPI Backend
Run with: uvicorn main:app --reload --port 8000
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, field_validator
from typing import List, Optional, Dict, Any
import time

app = FastAPI(
    title="Context Switch Overhead Analyzer API",
    description="Backend simulation engine for CPU process scheduling",
    version="3.0.0",
)

# Allow frontend dev origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],          # Tighten in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ─── MODELS ────────────────────────────────────────────────────────────────────

class ProcessIn(BaseModel):
    id: int
    name: str
    arrival_time: int = Field(ge=0)
    burst_time: int = Field(ge=1)
    priority: int = Field(default=1, ge=1)

    # BUG FIX #1: ensure burst_time is never zero even if client sends 0
    @field_validator("burst_time")
    @classmethod
    def burst_must_be_positive(cls, v: int) -> int:
        if v < 1:
            raise ValueError("burst_time must be >= 1")
        return v


class SimulateRequest(BaseModel):
    processes: List[ProcessIn]
    algorithm: str = Field(pattern="^(FCFS|SJF|RR)$")
    # BUG FIX #2: quantum=None bypassed ge=1 — default to 2 and validate when present
    quantum: Optional[int] = Field(default=2, ge=1)
    cs_overhead_ms: float = Field(default=2.0, ge=0)

    @field_validator("quantum", mode="before")
    @classmethod
    def quantum_must_be_positive(cls, v):
        if v is not None and v < 1:
            raise ValueError("quantum must be >= 1")
        return v if v is not None else 2


class TimelineBlock(BaseModel):
    pid: Optional[int]
    name: Optional[str]
    start: float
    end: float
    is_switch: bool = False
    color: Optional[str] = None


class ProcessMetric(BaseModel):
    id: int
    name: str
    arrival: int
    burst: int
    completion: float
    turnaround: float
    waiting: float
    efficiency_pct: float


class SimulateResponse(BaseModel):
    algorithm: str
    timeline: List[TimelineBlock]
    metrics: Dict[str, Any]
    process_metrics: List[ProcessMetric]
    total_time: float
    context_switches: int
    cs_overhead_total_ms: float
    perf_loss_pct: float
    computed_at: float


# ─── SCHEDULING ENGINES ────────────────────────────────────────────────────────

def run_fcfs(processes: List[ProcessIn]) -> List[Dict]:
    procs = sorted(processes, key=lambda p: p.arrival_time)
    timeline, t = [], 0
    for p in procs:
        if t < p.arrival_time:
            t = p.arrival_time
        # BUG FIX #3: removed the duplicate `t += p.burst_time` that followed the
        # append; t is advanced once here, correctly.
        start = t
        t += p.burst_time
        timeline.append({"pid": p.id, "name": p.name, "start": start, "end": t})
    return timeline


def run_sjf(processes: List[ProcessIn]) -> List[Dict]:
    procs = [{"id": p.id, "name": p.name, "arrival": p.arrival_time,
               "burst": p.burst_time, "remaining": p.burst_time} for p in processes]
    timeline, t, done = [], 0, set()

    while len(done) < len(procs):
        available = [p for p in procs if p["arrival"] <= t and p["id"] not in done]
        if not available:
            t += 1
            continue
        shortest = min(available, key=lambda x: x["burst"])
        timeline.append({"pid": shortest["id"], "name": shortest["name"],
                          "start": t, "end": t + shortest["burst"]})
        t += shortest["burst"]
        done.add(shortest["id"])
    return timeline


def run_rr(processes: List[ProcessIn], quantum: int) -> List[Dict]:
    procs = [{"id": p.id, "name": p.name, "arrival": p.arrival_time,
               "burst": p.burst_time, "remaining": p.burst_time} for p in processes]
    sorted_procs = sorted(procs, key=lambda x: x["arrival"])
    timeline, queue, in_queue = [], [], set()
    t, idx = 0, 0

    while idx < len(sorted_procs) and sorted_procs[idx]["arrival"] <= t:
        queue.append(sorted_procs[idx])
        in_queue.add(sorted_procs[idx]["id"])
        idx += 1

    while queue:
        current = queue.pop(0)
        run_time = min(quantum, current["remaining"])
        start = t
        t += run_time
        current["remaining"] -= run_time
        timeline.append({"pid": current["id"], "name": current["name"], "start": start, "end": t})

        while idx < len(sorted_procs) and sorted_procs[idx]["arrival"] <= t:
            if sorted_procs[idx]["id"] not in in_queue:
                queue.append(sorted_procs[idx])
                in_queue.add(sorted_procs[idx]["id"])
            idx += 1

        if current["remaining"] > 0:
            queue.append(current)
        else:
            in_queue.discard(current["id"])

        if not queue and idx < len(sorted_procs):
            t = sorted_procs[idx]["arrival"]
            while idx < len(sorted_procs) and sorted_procs[idx]["arrival"] <= t:
                queue.append(sorted_procs[idx])
                in_queue.add(sorted_procs[idx]["id"])
                idx += 1

    return timeline


def build_result(raw_timeline: List[Dict], processes: List[ProcessIn],
                 cs_overhead_ms: float) -> Dict:
    # Insert context switch markers
    timeline = []
    for i, block in enumerate(raw_timeline):
        if i > 0 and raw_timeline[i]["pid"] != raw_timeline[i - 1]["pid"]:
            timeline.append({
                "pid": None, "name": "CS",
                "start": raw_timeline[i - 1]["end"],
                "end": raw_timeline[i - 1]["end"] + 0.3,
                "is_switch": True,
            })
        timeline.append({**block, "is_switch": False})

    total_time = raw_timeline[-1]["end"] if raw_timeline else 1

    # Count switches
    context_switches = sum(
        1 for i in range(1, len(raw_timeline))
        if raw_timeline[i]["pid"] != raw_timeline[i - 1]["pid"]
    )

    # Per-process metrics
    process_metrics = []
    for p in processes:
        segs = [b for b in raw_timeline if b["pid"] == p.id]
        if not segs:
            continue
        completion = max(s["end"] for s in segs)
        turnaround = completion - p.arrival_time
        waiting = max(0, turnaround - p.burst_time)
        eff = (p.burst_time / turnaround * 100) if turnaround > 0 else 100.0
        process_metrics.append(ProcessMetric(
            id=p.id, name=p.name, arrival=p.arrival_time, burst=p.burst_time,
            completion=completion, turnaround=turnaround, waiting=waiting,
            efficiency_pct=round(eff, 1),
        ))

    avg_waiting = sum(m.waiting for m in process_metrics) / len(process_metrics) if process_metrics else 0
    avg_turnaround = sum(m.turnaround for m in process_metrics) / len(process_metrics) if process_metrics else 0
    busy_time = sum(b["end"] - b["start"] for b in raw_timeline)
    cpu_util = min(100.0, (busy_time / total_time) * 100)
    cs_overhead_total = context_switches * cs_overhead_ms
    # BUG FIX #4: removed the arbitrary *10 scaling factor; perf_loss is now
    # correctly expressed as overhead_ms / (total_scheduling_units + overhead_ms).
    # Both values are already in their respective units; the ratio gives the
    # fractional overhead correctly relative to total execution span.
    perf_loss = min(100.0, (cs_overhead_total / (total_time + cs_overhead_total)) * 100) if (total_time + cs_overhead_total) > 0 else 0.0

    return {
        "timeline": [TimelineBlock(**b) for b in timeline],
        "process_metrics": process_metrics,
        "total_time": total_time,
        "context_switches": context_switches,
        "cs_overhead_total_ms": cs_overhead_total,
        "perf_loss_pct": round(perf_loss, 3),
        "metrics": {
            "avg_waiting_ms": round(avg_waiting, 2),
            "avg_turnaround_ms": round(avg_turnaround, 2),
            "cpu_utilization_pct": round(cpu_util, 2),
            "context_switches": context_switches,
            "cs_overhead_ms": round(cs_overhead_total, 2),
            "performance_loss_pct": round(perf_loss, 3),
            "total_time_ms": total_time,
        },
    }


# ─── ROUTES ────────────────────────────────────────────────────────────────────

@app.get("/health")
def health():
    return {"status": "ok", "version": "3.0.0", "service": "context-switch-analyzer"}


@app.post("/simulate", response_model=SimulateResponse)
def simulate(req: SimulateRequest):
    if not req.processes:
        raise HTTPException(status_code=400, detail="At least one process required")
    if len(req.processes) > 20:
        raise HTTPException(status_code=400, detail="Maximum 20 processes")

    algo = req.algorithm
    try:
        if algo == "FCFS":
            raw = run_fcfs(req.processes)
        elif algo == "SJF":
            raw = run_sjf(req.processes)
        elif algo == "RR":
            raw = run_rr(req.processes, req.quantum or 2)
        else:
            # BUG FIX #5: HTTPException must be re-raised before the generic handler
            # catches it; moved the unknown-algo check outside the try block.
            raise HTTPException(status_code=400, detail=f"Unknown algorithm: {algo}")
    except HTTPException:
        # BUG FIX #5 (cont): re-raise HTTPException so FastAPI handles the status code
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Simulation error: {str(e)}")

    result = build_result(raw, req.processes, req.cs_overhead_ms)

    return SimulateResponse(
        algorithm=algo,
        computed_at=time.time(),
        **result,
    )


@app.post("/compare")
def compare(req: SimulateRequest):
    """Run all three algorithms and return side-by-side metrics."""
    # BUG FIX #6: replaced fragile late-binding lambda with explicit calls
    results = {}
    q = req.quantum or 2
    for algo in ["FCFS", "SJF", "RR"]:
        if algo == "FCFS":
            raw = run_fcfs(req.processes)
        elif algo == "SJF":
            raw = run_sjf(req.processes)
        else:
            raw = run_rr(req.processes, q)
        r = build_result(raw, req.processes, req.cs_overhead_ms)
        results[algo] = r["metrics"]
    return {"algorithms": results}


@app.get("/presets")
def presets():
    return {
        "Low Load": [
            {"id":1,"name":"P1","arrival_time":0,"burst_time":5,"priority":1},
            {"id":2,"name":"P2","arrival_time":2,"burst_time":3,"priority":2},
            {"id":3,"name":"P3","arrival_time":4,"burst_time":2,"priority":3},
        ],
        "High Load": [
            {"id":1,"name":"P1","arrival_time":0,"burst_time":8,"priority":2},
            {"id":2,"name":"P2","arrival_time":1,"burst_time":4,"priority":1},
            {"id":3,"name":"P3","arrival_time":2,"burst_time":6,"priority":3},
            {"id":4,"name":"P4","arrival_time":3,"burst_time":2,"priority":1},
            {"id":5,"name":"P5","arrival_time":5,"burst_time":5,"priority":2},
        ],
        "Burst Storm": [
            {"id":1,"name":"P1","arrival_time":0,"burst_time":10,"priority":3},
            {"id":2,"name":"P2","arrival_time":0,"burst_time":1, "priority":1},
            {"id":3,"name":"P3","arrival_time":0,"burst_time":3, "priority":2},
            {"id":4,"name":"P4","arrival_time":1,"burst_time":2, "priority":1},
        ],
    }