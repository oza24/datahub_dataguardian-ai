"""
Structured error taxonomy. Every failure path in the system — network, GraphQL,
matching, or LLM — is normalized into one of these codes instead of surfacing
raw exceptions or "Unknown GraphQL Error" to the user.
"""
from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field


class ErrorCode(str, Enum):
    DATASET_NOT_FOUND = "DATASET_NOT_FOUND"
    FIELD_NOT_FOUND = "FIELD_NOT_FOUND"
    PERMISSION_DENIED = "PERMISSION_DENIED"
    METADATA_SERVICE_UNAVAILABLE = "METADATA_SERVICE_UNAVAILABLE"
    NETWORK_TIMEOUT = "NETWORK_TIMEOUT"
    GRAPHQL_VALIDATION_FAILED = "GRAPHQL_VALIDATION_FAILED"
    MUTATION_REJECTED = "MUTATION_REJECTED"
    SCHEMA_MISMATCH = "SCHEMA_MISMATCH"
    AUTHENTICATION_FAILURE = "AUTHENTICATION_FAILURE"
    RATE_LIMITED = "RATE_LIMITED"
    CONFLICT = "CONFLICT"
    ALREADY_EXISTS = "ALREADY_EXISTS"
    AMBIGUOUS_ENTITY = "AMBIGUOUS_ENTITY"
    LOW_CONFIDENCE_INTENT = "LOW_CONFIDENCE_INTENT"
    UNKNOWN = "UNKNOWN"


class GovernanceError(BaseModel):
    error_code: ErrorCode
    reason: str
    suggestion: Optional[str] = None
    recoverable: bool = False
    candidates: list[str] = Field(default_factory=list)

    def to_markdown(self) -> str:
        lines = [f"\u274c {self.error_code.value.replace('_', ' ').title()}", "", f"Reason: {self.reason}"]
        if self.candidates:
            lines.append("")
            lines.append("Did you mean:")
            lines.extend(f"- {c}" for c in self.candidates)
        if self.suggestion:
            lines.append("")
            lines.append(f"Suggestion: {self.suggestion}")
        return "\n".join(lines)
