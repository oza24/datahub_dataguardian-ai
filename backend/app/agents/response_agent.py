"""Formats the final answer. Deliberately deterministic Python string
formatting rather than another LLM call — a governance mutation's
confirmation message should be exact and reproducible, not paraphrased."""
from langchain_core.messages import AIMessage

from app.state.graph_state import GraphState


def _format_action(state: GraphState) -> str:
    result = state.get("action_result") or {}
    schema = state.get("dataset_schema")
    table = schema.table_name if schema else state.get("resolved_table_name", "dataset")
    field = state.get("resolved_field_path")

    if result.get("success"):
        verified = result.get("verified")
        lines = [
            "\u2713 Description Updated Successfully" if verified else "\u2713 Description Updated (verification pending)",
            "",
            f"Dataset: {table}",
        ]
        if field:
            lines.append(f"Column: {field}")
        lines += [
            f"Platform: {schema.platform.title() if schema else 'Unknown'}",
            f"New Description: {result.get('description')}",
            f"Verification: {'Success' if verified else 'Could not confirm'}",
        ]
        return "\n".join(lines)

    return "\u274c Update Failed\n\nThe mutation did not complete successfully."


def _format_schema(state: GraphState) -> str:
    schema = state.get("dataset_schema")
    if not schema:
        return "No schema could be retrieved."
    lines = [f"Schema for {schema.table_name} ({schema.platform}):", ""]
    for f in schema.fields:
        desc = f" \u2014 {f.description}" if f.description else ""
        lines.append(f"- {f.field_path} ({f.native_type}){desc}")
    return "\n".join(lines)


def _format_impact(state: GraphState) -> str:
    report = state.get("impact_report") or {}
    return (
        f"Impact Analysis for {state.get('resolved_table_name', 'dataset')}:\n\n"
        f"Risk Score: {report.get('risk_score', 0)}/100 ({report.get('risk_level', 'UNKNOWN')})\n"
        f"Downstream assets affected: {report.get('total_impacted', 0)}\n"
        f"Dashboards impacted: {len(report.get('affected_dashboards', []))}\n"
        f"Models impacted: {len(report.get('affected_models', []))}"
    )


def _format_codegen(state: GraphState) -> str:
    code = state.get("generated_code")
    if not code:
        return "Could not generate code without a verified schema."
    return f"Generated dbt model:\n```sql\n{code}\n```"


_FORMATTERS = {
    "ACTION": _format_action,
    "SCHEMA": _format_schema,
    "IMPACT": _format_impact,
    "LINEAGE": _format_impact,
    "CODEGEN": _format_codegen,
}


def response_agent_node(state: GraphState) -> dict:
    if state.get("clarification_needed"):
        return {"messages": [AIMessage(content=state["clarification_needed"])]}

    if state.get("error"):
        return {"messages": [AIMessage(content=state["error"].to_markdown())]}

    intent = state.get("intent")
    intent_type = intent.intent if intent else "UNKNOWN"
    formatter = _FORMATTERS.get(intent_type)
    content = (
        formatter(state)
        if formatter
        else "I couldn't determine how to help with that. Could you rephrase it in terms of a table, column, or governance action?"
    )
    return {"messages": [AIMessage(content=content)]}
