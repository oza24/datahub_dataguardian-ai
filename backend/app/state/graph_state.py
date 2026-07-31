"""
Single LangGraph state definition. Every field is written by exactly one
agent and read by whichever agents need it downstream — no duplicated
"same fact, two keys" state like the old target_urn/schema_metadata pairing
that different nodes half-trusted.
"""
from typing import Annotated, Any, Optional, TypedDict

from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages

from app.models.errors import GovernanceError
from app.models.schemas import DatasetSchema, IntentExtraction


class GraphState(TypedDict, total=False):
    messages: Annotated[list[BaseMessage], add_messages]

    user_prompt: str
    intent: Optional[IntentExtraction]

    resolved_table_urn: Optional[str]
    resolved_table_name: Optional[str]
    resolved_field_path: Optional[str]

    dataset_schema: Optional[DatasetSchema]
    lineage: Optional[dict[str, Any]]
    impact_report: Optional[dict[str, Any]]
    generated_code: Optional[str]
    action_result: Optional[dict[str, Any]]

    error: Optional[GovernanceError]
    clarification_needed: Optional[str]
    retries: int
