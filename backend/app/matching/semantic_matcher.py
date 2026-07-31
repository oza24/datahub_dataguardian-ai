"""
Ranks arbitrary string candidates against a user's raw phrase by embedding
similarity. Used both for table resolution and field resolution — no
if/elif alias chains, no hardcoded lists.
"""
import logging
from dataclasses import dataclass
from typing import Optional, Sequence

from app.services.embedding_service import embedding_service

logger = logging.getLogger(__name__)


@dataclass
class MatchCandidate:
    value: str
    score: float


def rank_candidates(query: str, candidates: Sequence[str]) -> list[MatchCandidate]:
    if not candidates:
        return []
    query_vec = embedding_service.embed(query)
    scored = [
        MatchCandidate(value=c, score=embedding_service.cosine_similarity(query_vec, embedding_service.embed(c)))
        for c in candidates
    ]
    scored.sort(key=lambda m: m.score, reverse=True)
    return scored


def best_match(query: str, candidates: Sequence[str], threshold: float) -> tuple[Optional[str], float, list[MatchCandidate]]:
    """Returns (matched_value_or_None, top_score, ranked_candidates).
    Returns None for the match when the top score is below `threshold` —
    the caller must then ask the user rather than guess."""
    ranked = rank_candidates(query, candidates)
    if not ranked:
        return None, 0.0, []
    top = ranked[0]
    if top.score >= threshold:
        return top.value, top.score, ranked[:5]
    return None, top.score, ranked[:5]
