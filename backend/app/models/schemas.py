"""
Structured-output contracts for the LLM layer and for catalog data. These are
what `with_structured_output` binds to — the model is forced to answer in
this shape, which is what replaces regex/keyword extraction.
"""
from typing import Literal, Optional
from pydantic import BaseModel, Field

IntentType = Literal["ACTION", "SCHEMA", "IMPACT", "LINEAGE", "CODEGEN", "CLARIFY", "UNKNOWN"]


class IntentExtraction(BaseModel):
    intent: IntentType = Field(
        description=(
            "ACTION: create/update/set/rename/drop a description or other metadata field. "
            "SCHEMA: inspect/view/list a table's columns or structure. "
            "IMPACT: blast radius / risk of a change or drop. "
            "LINEAGE: upstream/downstream dependencies without a full risk score. "
            "CODEGEN: generate SQL or a dbt model. "
            "CLARIFY: governance-related but too vague to act on safely. "
            "UNKNOWN: unrelated to data governance."
        )
    )
    raw_table_phrase: Optional[str] = Field(
        default=None,
        description="The exact phrase the user used for a table/dataset, in their own words/script. Null if not mentioned. Do not normalize or translate it.",
    )
    raw_field_phrase: Optional[str] = Field(
        default=None,
        description="The exact phrase the user used for a column/field, in their own words/script. Null if not mentioned. Do not normalize or translate it.",
    )
    raw_platform_phrase: Optional[str] = Field(
        default=None, description="Platform mentioned by the user (snowflake, postgres, bigquery, mysql, etc.), or null."
    )
    new_description: Optional[str] = Field(
        default=None, description="Verbatim new description text the user wants applied, preserving original script. Null if not an ACTION with new text."
    )
    operation: Optional[str] = Field(
        default=None,
        description="Short verb phrase for the requested operation, e.g. 'update_description', 'view_schema', 'compute_impact', 'generate_dbt_model', 'drop_field'.",
    )
    detected_language: Optional[str] = Field(
        default=None, description="Best-guess register: 'english', 'hindi', 'hinglish', 'mixed', etc."
    )
    confidence: float = Field(ge=0.0, le=1.0, description="Your own confidence 0-1 that intent + entities were extracted correctly.")
    missing_information: list[str] = Field(
        default_factory=list, description="Pieces of information still needed to safely act, e.g. ['target_table']. Populate instead of guessing."
    )


class SchemaFieldInfo(BaseModel):
    field_path: str
    native_type: str = "STRING"
    nullable: bool = True
    description: Optional[str] = None


class DatasetSchema(BaseModel):
    urn: str
    table_name: str
    platform: str
    fields: list[SchemaFieldInfo] = Field(default_factory=list)
