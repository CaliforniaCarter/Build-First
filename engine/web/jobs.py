"""In-memory jobs + an event queue per job, so a worker thread can stream to an SSE route.

A generation blocks on `claude` subprocesses for tens of seconds; we run it off the event
loop in a thread and push progress events onto a thread-safe queue the SSE route drains.
"""

from __future__ import annotations

import queue
import threading
import uuid
from dataclasses import dataclass, field

# Sentinel event marking the end of a job's stream.
END = "__end__"


@dataclass
class Job:
    id: str
    kind: str  # "onboard" | "generate"
    run_id: str | None = None
    status: str = "running"  # running | done | error
    result: dict | None = None
    error: str | None = None
    q: "queue.Queue[dict]" = field(default_factory=queue.Queue)

    def emit(self, event: str, payload: dict | None = None) -> None:
        self.q.put({"event": event, **(payload or {})})

    def finish(self, status: str, *, result: dict | None = None, error: str | None = None) -> None:
        self.status = status
        self.result = result
        self.error = error
        self.q.put({"event": END, "status": status})


class JobRegistry:
    def __init__(self) -> None:
        self._jobs: dict[str, Job] = {}
        self._lock = threading.Lock()

    def create(self, kind: str, run_id: str | None = None) -> Job:
        job = Job(id=uuid.uuid4().hex, kind=kind, run_id=run_id)
        with self._lock:
            self._jobs[job.id] = job
        return job

    def get(self, job_id: str) -> Job | None:
        with self._lock:
            return self._jobs.get(job_id)


def run_in_thread(target, *args, **kwargs) -> threading.Thread:
    t = threading.Thread(target=target, args=args, kwargs=kwargs, daemon=True)
    t.start()
    return t
