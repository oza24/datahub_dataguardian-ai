"""
The ONLY layer that talks to DataHub GMS. Every method returns
(data, GovernanceError | None) — callers check the error, never a raw
exception, and this file never returns fabricated/fallback schema data:
a lookup failure is always surfaced as a GovernanceError, not fake fields.
"""
import logging
from typing import Any, Optional

import requests

from app.config import settings
from app.errors.classifier import classify_graphql_error, classify_network_exception
from app.graphql import mutations, queries
from app.models.errors import ErrorCode, GovernanceError
from app.models.schemas import DatasetSchema, SchemaFieldInfo

logger = logging.getLogger(__name__)


class DataHubRepository:
    def __init__(self) -> None:
        self.gms_url = settings.DATAHUB_GMS_URL.rstrip("/")
        self._headers = {"Content-Type": "application/json"}
        if settings.DATAHUB_GMS_TOKEN:
            self._headers["Authorization"] = f"Bearer {settings.DATAHUB_GMS_TOKEN}"

    def _execute(self, query: str, variables: dict) -> tuple[Optional[dict], Optional[GovernanceError]]:
        try:
            res = requests.post(
                f"{self.gms_url}/api/graphql",
                json={"query": query, "variables": variables},
                headers=self._headers,
                timeout=settings.GRAPHQL_TIMEOUT_SECONDS,
            )
        except requests.exceptions.RequestException as exc:
            return None, classify_network_exception(exc)

        if res.status_code == 401:
            return None, GovernanceError(error_code=ErrorCode.AUTHENTICATION_FAILURE, reason="DataHub GMS rejected credentials.")
        if res.status_code == 403:
            return None, GovernanceError(error_code=ErrorCode.PERMISSION_DENIED, reason="DataHub GMS denied permission for this operation.")
        if res.status_code == 429:
            return None, GovernanceError(error_code=ErrorCode.RATE_LIMITED, reason="DataHub GMS rate-limited this request.", recoverable=True)
        if res.status_code >= 500:
            return None, GovernanceError(
                error_code=ErrorCode.METADATA_SERVICE_UNAVAILABLE, reason=f"DataHub GMS returned HTTP {res.status_code}.", recoverable=True
            )
        if res.status_code != 200:
            return None, GovernanceError(error_code=ErrorCode.UNKNOWN, reason=f"DataHub GMS returned HTTP {res.status_code}: {res.text[:300]}")

        payload = res.json()
        if payload.get("errors"):
            msg = payload["errors"][0].get("message", "Unknown GraphQL error")
            return payload, classify_graphql_error(msg)
        return payload, None

    def search_datasets(self, query_str: str, limit: int = None) -> tuple[list[dict[str, Any]], Optional[GovernanceError]]:
        limit = limit or settings.DATASET_SEARCH_CANDIDATE_LIMIT
        data, err = self._execute(
            queries.SEARCH_DATASETS, {"input": {"type": "DATASET", "query": query_str, "start": 0, "count": limit}}
        )
        if err:
            return [], err

        results = ((data or {}).get("data", {}).get("search") or {}).get("searchResults", []) or []
        entities: list[dict[str, Any]] = []
        for r in results:
            entity = r.get("entity", {})
            name = entity.get("name") or (entity.get("properties") or {}).get("name") or entity.get("urn")
            entities.append({"urn": entity.get("urn"), "name": name})
        return entities, None

    def get_dataset_schema(self, dataset_urn: str) -> tuple[Optional[DatasetSchema], Optional[GovernanceError]]:
        data, err = self._execute(queries.GET_DATASET_SCHEMA, {"urn": dataset_urn})
        if err:
            return None, err

        dataset = ((data or {}).get("data") or {}).get("dataset")
        if not dataset:
            return None, GovernanceError(
                error_code=ErrorCode.DATASET_NOT_FOUND,
                reason=f"No dataset found in DataHub for URN '{dataset_urn}'.",
                suggestion="Verify the table name and try again.",
            )

        schema_meta = dataset.get("schemaMetadata") or {}
        fields_raw = schema_meta.get("fields") or []
        schema = DatasetSchema(
            urn=dataset_urn,
            table_name=dataset.get("name") or dataset_urn,
            platform=(dataset.get("platform") or {}).get("name", "unknown"),
            fields=[
                SchemaFieldInfo(
                    field_path=f.get("fieldPath", ""),
                    native_type=str(f.get("nativeDataType") or "STRING"),
                    nullable=f.get("nullable", True),
                    description=f.get("description"),
                )
                for f in fields_raw
            ],
        )
        return schema, None

    def get_lineage(self, dataset_urn: str, direction: str = "DOWNSTREAM") -> tuple[dict[str, Any], Optional[GovernanceError]]:
        data, err = self._execute(
            queries.GET_LINEAGE, {"input": {"urn": dataset_urn, "direction": direction, "start": 0, "count": 50}}
        )
        if err:
            return {"upstream": [], "downstream": []}, err

        results = ((data or {}).get("data", {}).get("searchAcrossLineage") or {}).get("searchResults", []) or []
        entities = [r["entity"] for r in results if r.get("entity")]
        key = "downstream" if direction == "DOWNSTREAM" else "upstream"
        return {"upstream": [], "downstream": [], key: entities}, None

    def update_description(
        self, resource_urn: str, description: str, field_path: Optional[str] = None
    ) -> tuple[bool, Optional[GovernanceError]]:
        payload_input: dict[str, Any] = {"description": description, "resourceUrn": resource_urn}
        if field_path:
            payload_input["subResource"] = field_path
            payload_input["subResourceType"] = "DATASET_FIELD"

        data, err = self._execute(mutations.UPDATE_DESCRIPTION, {"input": payload_input})
        if err:
            return False, err

        success = bool((data or {}).get("data", {}).get("updateDescription"))
        if not success:
            return False, GovernanceError(
                error_code=ErrorCode.MUTATION_REJECTED,
                reason="DataHub GMS accepted the request but reported no change applied.",
                recoverable=True,
            )
        return True, None


datahub_repository = DataHubRepository()
