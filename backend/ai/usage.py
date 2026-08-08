from __future__ import annotations

from dataclasses import dataclass, field

from .models import AIUsage


@dataclass
class AIUsageTracker:
    """In-memory provider/model usage accumulator."""

    totals: AIUsage = field(default_factory=AIUsage)
    by_provider: dict[str, AIUsage] = field(default_factory=dict)
    by_model: dict[str, AIUsage] = field(default_factory=dict)

    @staticmethod
    def _merge(target: AIUsage, usage: AIUsage) -> None:
        target.input_tokens += int(usage.input_tokens)
        target.output_tokens += int(usage.output_tokens)
        target.total_tokens += int(usage.total_tokens)
        target.estimated_cost_usd += float(usage.estimated_cost_usd)

    def record(self, provider: str, model: str, usage: AIUsage | None) -> None:
        if usage is None:
            return
        self._merge(self.totals, usage)
        provider_key = str(provider or "unknown")
        model_key = str(model or "unknown")
        self._merge(self.by_provider.setdefault(provider_key, AIUsage()), usage)
        self._merge(self.by_model.setdefault(model_key, AIUsage()), usage)

    def snapshot(self) -> dict:
        def as_dict(value: AIUsage) -> dict:
            return {
                "input_tokens": value.input_tokens,
                "output_tokens": value.output_tokens,
                "total_tokens": value.total_tokens,
                "estimated_cost_usd": value.estimated_cost_usd,
            }

        return {
            "totals": as_dict(self.totals),
            "by_provider": {key: as_dict(value) for key, value in self.by_provider.items()},
            "by_model": {key: as_dict(value) for key, value in self.by_model.items()},
        }
