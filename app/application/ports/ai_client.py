"""
Abstract port for AI completion clients.
"""

from abc import ABC, abstractmethod
from typing import Optional

from pydantic import BaseModel


class AIMessage(BaseModel):
    role: str  # "user" | "assistant" | "system"
    content: str


class AIResponse(BaseModel):
    content: str
    model: str
    provider: str
    tokens_used: Optional[int] = None


class AIClient(ABC):
    """Port interface implemented by each AI provider adapter."""

    # @MX:ANCHOR: [AUTO] Central AI port - all provider clients implement this interface
    # @MX:REASON: Swapping providers only requires a new AIClient impl; callers are stable

    @abstractmethod
    async def complete(
        self,
        messages: list[AIMessage],
        temperature: float = 0.7,
        max_tokens: int = 2000,
        **kwargs,
    ) -> AIResponse:
        """Send a chat-completion request and return a structured response."""

    @abstractmethod
    async def vision_complete(
        self,
        messages: list[AIMessage],
        image_paths: list[str],
        temperature: float = 0.7,
        max_tokens: int = 2000,
        **kwargs,
    ) -> AIResponse:
        """Send a vision-capable chat-completion request."""
