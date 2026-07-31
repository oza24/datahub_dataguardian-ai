import logging
import traceback

from dotenv import load_dotenv

load_dotenv()

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from langchain_core.messages import HumanMessage
from pydantic import BaseModel

from app.graph.workflow import agent_app

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="DataGuardian AI Copilot")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class ChatRequest(BaseModel):
    prompt: str


@app.get("/health")
def health():
    return {"status": "healthy"}


_INTENT_TO_FRONTEND_AGENT = {
    "ACTION": "action_agent",
    "SCHEMA": "schema_agent",
    "IMPACT": "impact_agent",
    "LINEAGE": "lineage_agent",
    "CODEGEN": "codegen_agent",
}


@app.post("/api/chat")
async def chat(request: ChatRequest):
    try:
        initial_state = {"messages": [HumanMessage(content=request.prompt)]}
        result = agent_app.invoke(initial_state)

        final_messages = [m for m in result.get("messages", []) if not isinstance(m, HumanMessage)]
        content = final_messages[-1].content if final_messages else "No response generated."

        intent = result.get("intent")
        impact_report = result.get("impact_report")

        # The frontend's ExecutionTrace component reads `trace: [{agent, content, state}]`.
        # The new pipeline emits one final formatted message rather than a message per
        # agent, so we surface that single step under whichever agent card fits the
        # intent (falling back to "Supervisor Router" for CLARIFY/UNKNOWN/errors).
        trace = [
            {
                "agent": _INTENT_TO_FRONTEND_AGENT.get(intent.intent) if intent else None,
                "content": content,
                "state": {
                    "risk_score": impact_report.get("risk_score") if impact_report else None,
                    "has_code": bool(result.get("generated_code")),
                },
            }
        ]

        return {
            "status": "success",
            "reply": content,
            "trace": trace,
            "intent": intent.intent if intent else None,
            "confidence": intent.confidence if intent else None,
            "resolved_table": result.get("resolved_table_name"),
            "resolved_field": result.get("resolved_field_path"),
        }
    except Exception as exc:
        logger.error("Agent execution failed", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Agent execution error: {exc}")
