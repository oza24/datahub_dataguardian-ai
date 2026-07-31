"""
Thin wrapper around the chat LLM. Every agent that needs reasoning goes
through here instead of instantiating its own ChatGoogleGenerativeAI, so
model config (temperature, retries, model name) is set in exactly one place.
"""
import logging
from typing import Type, TypeVar

from langchain_google_genai import ChatGoogleGenerativeAI
from pydantic import BaseModel

from app.config import settings

logger = logging.getLogger(__name__)
T = TypeVar("T", bound=BaseModel)


class LLMService:
    def __init__(self) -> None:
        self._llm = ChatGoogleGenerativeAI(
            model=settings.GEMINI_CHAT_MODEL,
            google_api_key=settings.GEMINI_API_KEY,
            temperature=0.0,
            max_retries=2,
        )

    def structured(self, schema: Type[T], system_prompt: str, user_prompt: str) -> T:
        """Force the model to answer in `schema`'s shape. This is what replaces
        regex/keyword extraction entirely."""
        structured_llm = self._llm.with_structured_output(schema)
        return structured_llm.invoke([("system", system_prompt), ("human", user_prompt)])

    def raw(self, system_prompt: str, user_prompt: str) -> str:
        response = self._llm.invoke([("system", system_prompt), ("human", user_prompt)])
        return response.content


llm_service = LLMService()
