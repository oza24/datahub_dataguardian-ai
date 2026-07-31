"""Understands what the user wants. This is the only place natural language
is turned into structure — via LLM structured output, not regex."""
import logging

from app.models.schemas import IntentExtraction
from app.prompts.intent_prompts import INTENT_SYSTEM_PROMPT
from app.services.llm_service import llm_service
from app.state.graph_state import GraphState

logger = logging.getLogger(__name__)


def intent_agent_node(state: GraphState) -> dict:
    prompt = state["user_prompt"]
    try:
        intent = llm_service.structured(IntentExtraction, INTENT_SYSTEM_PROMPT, prompt)
    except Exception:
        logger.exception("Intent extraction failed")
        intent = IntentExtraction(intent="UNKNOWN", confidence=0.0, missing_information=["intent"])
    return {"intent": intent}
