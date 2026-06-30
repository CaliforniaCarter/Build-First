"""Posts — the feed/home history, plus approve (the human gate) and edit + re-score."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from engine.ablation import load_layers
from engine.providers.anthropic import AnthropicProvider
from engine.rubric.shared import build_score_prompt, parse_score

from .. import store
from ..deps import get_provider, read_persona
from ..schemas import PostPatch, serialize_score

router = APIRouter(prefix="/api/posts", tags=["posts"])


@router.get("")
def list_posts(status: str | None = None) -> dict:
    return {"posts": store.list_posts(status)}


@router.get("/{post_id}")
def get_post(post_id: str) -> dict:
    post = store.get_post(post_id)
    if post is None:
        raise HTTPException(status_code=404, detail="post not found")
    return post


@router.post("/{post_id}/approve")
def approve(post_id: str) -> dict:
    """The human gate — drafts only; approving never posts anywhere, just flips status."""
    post = store.update_post(post_id, status="approved")
    if post is None:
        raise HTTPException(status_code=404, detail="post not found")
    return post


@router.post("/{post_id}/posted")
def mark_posted(post_id: str) -> dict:
    """You posted it yourself — log it (Timbre never posts for you). Returns the shipped tally."""
    post = store.update_post(post_id, status="posted")
    if post is None:
        raise HTTPException(status_code=404, detail="post not found")
    shipped = sum(1 for p in store.list_posts() if p.get("status") == "posted")
    return {"post": post, "shipped": shipped}


@router.patch("/{post_id}")
def patch_post(
    post_id: str,
    body: PostPatch,
    provider: AnthropicProvider = Depends(get_provider),
) -> dict:
    post = store.get_post(post_id)
    if post is None:
        raise HTTPException(status_code=404, detail="post not found")

    fields: dict = {}
    new_body = body.body if body.body is not None else post["body"]
    if body.body is not None:
        fields["body"] = new_body

    if body.rescore:
        persona = read_persona() or "(no persona)"
        layers = load_layers()
        score = parse_score(
            provider.complete("score", build_score_prompt(new_body, persona, layers, None))
        )
        fields["score"] = serialize_score(score)

    if not fields:
        return post
    return store.update_post(post_id, **fields)
