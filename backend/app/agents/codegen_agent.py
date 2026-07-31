"""Generates a dbt staging model grounded strictly in the verified live
schema — every column in the output came from DataHub, never invented."""
from app.state.graph_state import GraphState


def codegen_agent_node(state: GraphState) -> dict:
    schema = state.get("dataset_schema")
    if not schema or not schema.fields:
        return {}

    cols_sql = ",\n".join(f"    {f.field_path}" for f in schema.fields)
    code = f"""-- Production dbt staging model (schema-verified via DataHub)
-- Source URN: {schema.urn}

with raw_source as (
    select * from {{{{ source('{schema.platform}', '{schema.table_name}') }}}}
),

transformed as (
    select
{cols_sql}
    from raw_source
)

select * from transformed
"""
    return {"generated_code": code}
