"""Executes the live GraphQL mutation. Self-healing: on a recoverable error
(e.g. transient GMS unavailability, conflict) it retries up to
MAX_MUTATION_RETRIES; on a non-recoverable error it stops and lets the
Response agent explain why, rather than retrying blindly."""
import logging

from app.config import settings
from app.repositories.datahub_repository import datahub_repository
from app.state.graph_state import GraphState

logger = logging.getLogger(__name__)


def action_agent_node(state: GraphState) -> dict:
    intent = state.get("intent")
    urn = state.get("resolved_table_urn")
    if not intent or intent.intent != "ACTION" or not urn:
        return {}

    description = intent.new_description or ""
    field_path = state.get("resolved_field_path")

    attempt = 0
    last_err = None
    while attempt <= settings.MAX_MUTATION_RETRIES:
        success, err = datahub_repository.update_description(urn, description, field_path)
        if success:
            return {"action_result": {"success": True, "field_path": field_path, "description": description}}
        last_err = err
        if not err or not err.recoverable:
            break
        attempt += 1
        logger.info("Self-healing retry %d for URN=%s after error: %s", attempt, urn, err.error_code)

    return {"error": last_err, "action_result": {"success": False}}
