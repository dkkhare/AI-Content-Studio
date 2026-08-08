from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(slots=True)
class AIMessage:
    role: str
    content: str


@dataclass(slots=True)
class AIRequest:
    messages: list[AIMessage] = field(default_factory=list)
    model: str = ""
    temperature: float | None = None
    max_output_tokens: int | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_prompt(
        cls,
        prompt: str,
        *,
        system: str | None = None,
        model: str = "",
        **kwargs,
    ) -> "AIRequest":
        messages: list[AIMessage] = []
        if system:
            messages.append(AIMessage("system", str(system)))
        messages.append(AIMessage("user", str(prompt)))
        return cls(messages=messages, model=model, **kwargs)


@dataclass(slots=True)
class AIUsage:
    input_tokens: int = 0
    output_tokens: int = 0
    total_tokens: int = 0
    estimated_cost_usd: float = 0.0

    def __post_init__(self) -> None:
        if not self.total_tokens:
            self.total_tokens = int(self.input_tokens) + int(self.output_tokens)


@dataclass(slots=True)
class AIResponse:
    text: str
    provider: str
    model: str = ""
    usage: AIUsage = field(default_factory=AIUsage)
    raw: Any = None


@dataclass(slots=True)
class AIStreamChunk:
    text: str = ""
    provider: str = ""
    model: str = ""
    done: bool = False
    usage: AIUsage | None = None
    raw: Any = None
