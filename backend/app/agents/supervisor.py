"""Entry node: pulls the latest human message into flat state fields the
rest of the pipeline reads. No routing decisions live here anymore —
routing is expressed as LangGraph conditional edges in graph/workflow.py."""
import logging

from langchain_core.messages import HumanMessage

from app.state.graph_state import GraphState

logger = logging.getLogger(__name__)


def supervisor_node(state: GraphState) -> dict:
    human_msgs = [m for m in state.get("messages", []) if isinstance(m, HumanMessage)]
    prompt = human_msgs[-1].content if human_msgs else ""
    logger.info("Supervisor received prompt: %s", prompt[:120])
    return {"user_prompt": prompt, "retries": 0}
