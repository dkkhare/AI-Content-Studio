from __future__ import annotations

from dataclasses import dataclass, field
import re

from ..models import AIMessage, AIRequest

_VARIABLE_RE = re.compile(r"{{\s*([A-Za-z_][A-Za-z0-9_]*)\s*}}")


class PromptRenderError(ValueError):
    pass


@dataclass(frozen=True, slots=True)
class PromptTemplate:
    name: str
    version: str
    user_template: str
    system_template: str = ""
    description: str = ""
    defaults: dict[str, str] = field(default_factory=dict)
    model: str = ""

    @property
    def variables(self) -> set[str]:
        return set(_VARIABLE_RE.findall(self.user_template + "\n" + self.system_template))

    def render(self, variables: dict | None = None, *, model: str = "", **request_options) -> AIRequest:
        values = dict(self.defaults)
        values.update(variables or {})
        missing = sorted(name for name in self.variables if name not in values)
        if missing:
            raise PromptRenderError(
                f"Prompt '{self.name}' is missing required variable(s): {', '.join(missing)}"
            )

        def replace(match: re.Match) -> str:
            return str(values[match.group(1)])

        system = _VARIABLE_RE.sub(replace, self.system_template).strip()
        user = _VARIABLE_RE.sub(replace, self.user_template).strip()
        messages = []
        if system:
            messages.append(AIMessage("system", system))
        messages.append(AIMessage("user", user))
        return AIRequest(
            messages=messages,
            model=model or self.model,
            **request_options,
        )
