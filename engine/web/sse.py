"""Server-Sent Events helper — drain a Job's queue to the browser, with heartbeats.

The queue is a blocking, thread-safe `queue.Queue`; we bridge it onto the event loop with
`asyncio.to_thread` so a slow generation never stalls the server. Heartbeat comment frames
keep the connection open through quiet stretches, and we stop if the client disconnects.
"""

from __future__ import annotations

import asyncio
import json
import queue

from fastapi import Request
from fastapi.responses import StreamingResponse

from .jobs import END, Job

_HEARTBEAT_SECONDS = 15.0


def sse_response(job: Job, request: Request) -> StreamingResponse:
    async def event_stream():
        yield ": connected\n\n"  # prime the stream so the browser opens it immediately
        while True:
            if await request.is_disconnected():
                break  # worker keeps running; result stays on the job for later retrieval
            try:
                ev = await asyncio.to_thread(job.q.get, True, _HEARTBEAT_SECONDS)
            except queue.Empty:
                yield ": ping\n\n"  # heartbeat
                continue
            if ev.get("event") == END:
                yield f"event: end\ndata: {json.dumps({'status': job.status})}\n\n"
                break
            yield f"data: {json.dumps(ev)}\n\n"

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
