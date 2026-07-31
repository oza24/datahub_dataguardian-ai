"""Pulls the ground-truth schema (and, for impact/lineage intents, the
lineage graph) for the resolved dataset. Never fabricates fields."""
from app.repositories.datahub_repository import datahub_repository
from app.state.graph_state import GraphState


def metadata_retrieval_agent_node(state: GraphState) -> dict:
    urn = state.get("resolved_table_urn")
    if not urn:
        return {}

    schema, err = datahub_repository.get_dataset_schema(urn)
    if err:
        return {"error": err}

    updates: dict = {"dataset_schema": schema}

    intent = state.get("intent")
    if intent and intent.intent in ("IMPACT", "LINEAGE"):
        lineage, lerr = datahub_repository.get_lineage(urn)
        if lerr:
            updates["error"] = lerr
        else:
            updates["lineage"] = lineage

    return updates
