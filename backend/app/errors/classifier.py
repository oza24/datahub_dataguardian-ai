"""
Translates raw exceptions and DataHub GraphQL error strings into the
GovernanceError taxonomy. This is the ONLY place error-message text is
pattern-matched, so classification logic isn't duplicated per-agent.
"""
import re
from typing import Optional

import requests

from app.models.errors import ErrorCode, GovernanceError

_PATTERNS: list[tuple[ErrorCode, list[str]]] = [
    (ErrorCode.AUTHENTICATION_FAILURE, [r"unauthorized", r"\b401\b", r"invalid token", r"authentication"]),
    (ErrorCode.PERMISSION_DENIED, [r"forbidden", r"\b403\b", r"permission", r"not authorized"]),
    (ErrorCode.RATE_LIMITED, [r"\b429\b", r"rate limit", r"too many requests"]),
    (ErrorCode.DATASET_NOT_FOUND, [r"entity.*not found", r"dataset.*not found", r"no such urn"]),
    (ErrorCode.FIELD_NOT_FOUND, [r"field.*not found", r"unknown field", r"no matching field"]),
    (ErrorCode.ALREADY_EXISTS, [r"already exists", r"duplicate"]),
    (ErrorCode.CONFLICT, [r"conflict", r"concurrent modification"]),
    (ErrorCode.SCHEMA_MISMATCH, [r"schema mismatch", r"type mismatch", r"incompatible type"]),
    (ErrorCode.GRAPHQL_VALIDATION_FAILED, [r"validation error", r"cannot query field", r"unknown argument", r"unknown type"]),
    (ErrorCode.MUTATION_REJECTED, [r"mutation.*rejected", r"failed to update", r"could not persist"]),
]

_RECOVERABLE = {
    ErrorCode.NETWORK_TIMEOUT,
    ErrorCode.METADATA_SERVICE_UNAVAILABLE,
    ErrorCode.RATE_LIMITED,
    ErrorCode.CONFLICT,
    ErrorCode.SCHEMA_MISMATCH,
    ErrorCode.MUTATION_REJECTED,
}

_SUGGESTIONS: dict[ErrorCode, str] = {
    ErrorCode.AUTHENTICATION_FAILURE: "Check the DataHub GMS token/credentials.",
    ErrorCode.PERMISSION_DENIED: "Request edit access to this entity from the DataHub admin.",
    ErrorCode.RATE_LIMITED: "Wait a few seconds and retry.",
    ErrorCode.SCHEMA_MISMATCH: "Re-fetch the live schema and retry with the correct field/enum.",
    ErrorCode.GRAPHQL_VALIDATION_FAILED: "The mutation shape may not match this DataHub GMS version; verify the subResourceType enum.",
}


def classify_network_exception(exc: Exception) -> GovernanceError:
    if isinstance(exc, requests.exceptions.Timeout):
        return GovernanceError(
            error_code=ErrorCode.NETWORK_TIMEOUT,
            reason="The request to DataHub GMS timed out.",
            suggestion="Retry shortly, or check GMS health.",
            recoverable=True,
        )
    if isinstance(exc, requests.exceptions.ConnectionError):
        return GovernanceError(
            error_code=ErrorCode.METADATA_SERVICE_UNAVAILABLE,
            reason="Could not connect to DataHub GMS.",
            suggestion="Confirm DATAHUB_GMS_URL is reachable and DataHub is running.",
            recoverable=True,
        )
    return GovernanceError(error_code=ErrorCode.UNKNOWN, reason=str(exc), recoverable=False)


def classify_graphql_error(message: str) -> GovernanceError:
    lowered = message.lower()
    for code, patterns in _PATTERNS:
        if any(re.search(p, lowered) for p in patterns):
            return GovernanceError(
                error_code=code,
                reason=message,
                suggestion=_SUGGESTIONS.get(code),
                recoverable=code in _RECOVERABLE,
            )
    return GovernanceError(error_code=ErrorCode.UNKNOWN, reason=message, recoverable=False)
