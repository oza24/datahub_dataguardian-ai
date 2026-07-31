"""Pure functions over a DatasetSchema — no I/O, easy to unit test."""
from app.models.schemas import DatasetSchema


def field_exists(schema: DatasetSchema, field_path: str) -> bool:
    return any(f.field_path == field_path for f in schema.fields)


def list_field_names(schema: DatasetSchema) -> list[str]:
    return [f.field_path for f in schema.fields]
