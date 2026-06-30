"""Timbre web API — a thin FastAPI layer over the engine.

It imports and reuses the engine pipeline (engine.*) and never reimplements it. The
front-end (web/) talks to this over JSON/REST; this process is the local backend, so
"runs on your machine" stays literally true.
"""
