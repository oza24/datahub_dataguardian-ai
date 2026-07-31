"""Resolves the user's raw field phrase against the LIVE schema field list
using semantic similarity. Replaces every 'email'/'cust email'/'ईमेल' style
alias branch with one embedding comparison against real catalog fields."""
from app.config import settings
from app.matching.semantic_matcher import best_match
from app.models.errors import ErrorCode, GovernanceError
from app.state.graph_state import GraphState
from app.validation.validators import list_field_names


def schema_validation_agent_node(state: GraphState) -> dict:
    intent = state.get("intent")
    schema = state.get("dataset_schema")
    if not intent or not schema:
        return {}

    if not intent.raw_field_phrase:
        return {}  # table-level operation; nothing to validate

    field_names = list_field_names(schema)
    if not field_names:
        return {
            "error": GovernanceError(
                error_code=ErrorCode.SCHEMA_MISMATCH,
                reason=f"'{schema.table_name}' has no fields registered in DataHub.",
            )
        }

    match_name, score, ranked = best_match(intent.raw_field_phrase, field_names, settings.FIELD_MATCH_CONFIDENCE_THRESHOLD)
    if not match_name:
        return {
            "error": GovernanceError(
                error_code=ErrorCode.FIELD_NOT_FOUND,
                reason=f"'{intent.raw_field_phrase}' does not match any column in '{schema.table_name}' (best score {score:.2f}).",
                suggestion="Did you mean one of these?",
                candidates=[r.value for r in ranked[:3]],
                recoverable=True,
            )
        }

    return {"resolved_field_path": match_name}
