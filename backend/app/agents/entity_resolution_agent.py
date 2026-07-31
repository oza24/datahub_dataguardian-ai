"""Resolves the table phrase the user gave into a real DataHub URN by
searching the catalog and semantically ranking the results — never by
looking the phrase up in a hardcoded alias table."""
import logging

from app.config import settings
from app.matching.semantic_matcher import best_match
from app.models.errors import ErrorCode, GovernanceError
from app.repositories.datahub_repository import datahub_repository
from app.state.graph_state import GraphState

logger = logging.getLogger(__name__)


def entity_resolution_agent_node(state: GraphState) -> dict:
    intent = state.get("intent")
    if not intent or not intent.raw_table_phrase:
        return {"clarification_needed": "Which table or dataset are you referring to?"}

    candidates, err = datahub_repository.search_datasets(intent.raw_table_phrase)
    if err:
        return {"error": err}

    if not candidates:
        return {
            "error": GovernanceError(
                error_code=ErrorCode.DATASET_NOT_FOUND,
                reason=f"No dataset in DataHub matches '{intent.raw_table_phrase}'.",
                suggestion="Check the spelling, or ask to list available tables.",
            )
        }

    candidate_names = [c["name"] or c["urn"] for c in candidates]
    match_name, score, ranked = best_match(
        intent.raw_table_phrase, candidate_names, settings.TABLE_MATCH_CONFIDENCE_THRESHOLD
    )

    if not match_name:
        return {
            "error": GovernanceError(
                error_code=ErrorCode.AMBIGUOUS_ENTITY,
                reason=f"Could not confidently match '{intent.raw_table_phrase}' to a table (best score {score:.2f}).",
                suggestion="Please confirm the exact table name.",
                candidates=[r.value for r in ranked[:3]],
                recoverable=True,
            )
        }

    matched = next(c for c in candidates if (c["name"] or c["urn"]) == match_name)
    return {"resolved_table_urn": matched["urn"], "resolved_table_name": match_name}
