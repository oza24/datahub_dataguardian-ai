"""Safety gate before any mutation: blocks on low-confidence intent or
missing required fields instead of letting the Action agent guess."""
from app.config import settings
from app.state.graph_state import GraphState


def decision_agent_node(state: GraphState) -> dict:
    if state.get("error"):
        return {}

    intent = state.get("intent")
    if not intent:
        return {"clarification_needed": "I couldn't understand that request — could you rephrase it?"}

    if intent.confidence < settings.INTENT_CONFIDENCE_THRESHOLD or intent.missing_information:
        missing = ", ".join(intent.missing_information) or "some details"
        return {"clarification_needed": f"I need a bit more detail before proceeding ({missing}). Could you confirm?"}

    if intent.intent == "ACTION" and not intent.new_description and intent.operation != "drop_field":
        return {"clarification_needed": "What should the new description say?"}

    return {}
