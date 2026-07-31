"""Turns the raw lineage graph into a risk score. Deterministic scoring —
no LLM here — because a risk number should be reproducible for the same
lineage graph, not vary between calls."""
from app.state.graph_state import GraphState


def impact_agent_node(state: GraphState) -> dict:
    lineage = state.get("lineage") or {}
    downstream = lineage.get("downstream", [])

    dashboards = [e for e in downstream if any(p in (e.get("urn") or "").lower() for p in ("looker", "tableau"))]
    models = [e for e in downstream if "mlflow" in (e.get("urn") or "").lower() or e.get("type") == "ML_MODEL"]

    risk_score = min(100, len(downstream) * 20 + len(dashboards) * 15)
    risk_level = "HIGH" if risk_score >= 70 else "MEDIUM" if risk_score >= 30 else "LOW"

    return {
        "impact_report": {
            "risk_score": risk_score,
            "risk_level": risk_level,
            "total_impacted": len(downstream),
            "affected_dashboards": [e.get("urn") for e in dashboards],
            "affected_models": [e.get("urn") for e in models],
        }
    }
