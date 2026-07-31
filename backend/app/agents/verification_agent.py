"""Re-reads the schema after a successful mutation to confirm the change was
actually persisted, instead of trusting the mutation's boolean response."""
from app.repositories.datahub_repository import datahub_repository
from app.state.graph_state import GraphState


def verification_agent_node(state: GraphState) -> dict:
    action_result = state.get("action_result")
    urn = state.get("resolved_table_urn")
    if not action_result or not action_result.get("success") or not urn:
        return {}

    schema, err = datahub_repository.get_dataset_schema(urn)
    if err:
        return {"error": err}

    field_path = state.get("resolved_field_path")
    verified = True
    verified_description = None
    if field_path:
        verified = False
        for f in schema.fields:
            if f.field_path == field_path:
                verified_description = f.description
                verified = f.description == action_result.get("description")
                break

    action_result = {**action_result, "verified": verified, "verified_description": verified_description}
    return {"action_result": action_result, "dataset_schema": schema}
