"""
Wires the nine single-responsibility agents into the LangGraph pipeline:

  Supervisor -> Intent -> Entity Resolution -> Metadata Retrieval
             -> Schema Validation -> Decision -> {Action -> Verification |
             Codegen | Impact | Schema-response} -> Response -> END

Every conditional edge is a short pure function of state, so the routing
logic is inspectable in one file instead of being interleaved with agent
bodies (as `next_agent` string-returns were in the old graph).
"""
from langgraph.graph import END, START, StateGraph

from app.agents.action_agent import action_agent_node
from app.agents.codegen_agent import codegen_agent_node
from app.agents.decision_agent import decision_agent_node
from app.agents.entity_resolution_agent import entity_resolution_agent_node
from app.agents.impact_agent import impact_agent_node
from app.agents.intent_agent import intent_agent_node
from app.agents.metadata_retrieval_agent import metadata_retrieval_agent_node
from app.agents.response_agent import response_agent_node
from app.agents.schema_validation_agent import schema_validation_agent_node
from app.agents.supervisor import supervisor_node
from app.agents.verification_agent import verification_agent_node
from app.state.graph_state import GraphState


def _after_intent(state: GraphState) -> str:
    intent = state.get("intent")
    if not intent or intent.intent in ("UNKNOWN", "CLARIFY"):
        return "response_agent"
    return "entity_resolution_agent"


def _route_after_entity_resolution(state: GraphState) -> str:
    return "response_agent" if state.get("error") else "metadata_retrieval_agent"


def _route_after_metadata(state: GraphState) -> str:
    return "response_agent" if state.get("error") else "schema_validation_agent"


def _route_after_validation(state: GraphState) -> str:
    return "response_agent" if state.get("error") else "decision_agent"


def _route_after_decision(state: GraphState) -> str:
    if state.get("error") or state.get("clarification_needed"):
        return "response_agent"
    intent = state.get("intent")
    mapping = {
        "ACTION": "action_agent",
        "CODEGEN": "codegen_agent",
        "IMPACT": "impact_agent",
        "LINEAGE": "impact_agent",
        "SCHEMA": "response_agent",
    }
    return mapping.get(intent.intent if intent else "", "response_agent")


def build_graph():
    workflow = StateGraph(GraphState)

    workflow.add_node("supervisor", supervisor_node)
    workflow.add_node("intent_agent", intent_agent_node)
    workflow.add_node("entity_resolution_agent", entity_resolution_agent_node)
    workflow.add_node("metadata_retrieval_agent", metadata_retrieval_agent_node)
    workflow.add_node("schema_validation_agent", schema_validation_agent_node)
    workflow.add_node("decision_agent", decision_agent_node)
    workflow.add_node("action_agent", action_agent_node)
    workflow.add_node("verification_agent", verification_agent_node)
    workflow.add_node("codegen_agent", codegen_agent_node)
    workflow.add_node("impact_agent", impact_agent_node)
    workflow.add_node("response_agent", response_agent_node)

    workflow.add_edge(START, "supervisor")
    workflow.add_edge("supervisor", "intent_agent")
    workflow.add_conditional_edges("intent_agent", _after_intent)
    workflow.add_conditional_edges("entity_resolution_agent", _route_after_entity_resolution)
    workflow.add_conditional_edges("metadata_retrieval_agent", _route_after_metadata)
    workflow.add_conditional_edges("schema_validation_agent", _route_after_validation)
    workflow.add_conditional_edges("decision_agent", _route_after_decision)
    workflow.add_edge("action_agent", "verification_agent")
    workflow.add_edge("verification_agent", "response_agent")
    workflow.add_edge("codegen_agent", "response_agent")
    workflow.add_edge("impact_agent", "response_agent")
    workflow.add_edge("response_agent", END)

    return workflow.compile()


agent_app = build_graph()
